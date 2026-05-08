import json
import re
import logging
from typing import Optional
from langchain_ollama import ChatOllama, OllamaLLM
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from app.db.session import SessionLocal
from app.repositories.schedule_repository import schedule_repo
from app.repositories.appointment_repository import appointment_repo

logger = logging.getLogger("app")

# ─────────────────────────────────────────────
# Tool Definitions
# ─────────────────────────────────────────────

@tool
async def list_departments() -> str:
    """List all available departments in the clinic."""
    try:
        async with SessionLocal() as db:
            from app.repositories.department_repository import department_repo as dr
            depts = await dr.get_multi(db)
            if not depts:
                return "No departments found."
            return json.dumps([{"id": d.id, "name": d.name} for d in depts])
    except Exception as e:
        logger.error(f"list_departments error: {e}")
        return f"Error: {str(e)}"


@tool
async def search_doctors(specialization: Optional[str] = None, name: Optional[str] = None) -> str:
    """Search for doctors by specialization or name. Returns a list of doctors with their IDs."""
    try:
        async with SessionLocal() as db:
            from app.repositories.doctor_repository import doctor_repo as dcr
            doctors = await dcr.search_doctors(db, specialization=specialization, search_query=name)
            if not doctors:
                return "No doctors found."
            return json.dumps([
                {"id": d.id, "name": d.user.full_name, "specialization": d.specialization, "fee": str(d.consultation_fee)}
                for d in doctors
            ])
    except Exception as e:
        logger.error(f"search_doctors error: {e}")
        return f"Error: {str(e)}"


@tool
async def get_available_slots(doctor_id: int, date: str) -> str:
    """Get available appointment slots for a doctor on a specific date (YYYY-MM-DD)."""
    try:
        from datetime import date as date_type
        query_date = date_type.fromisoformat(date)
        async with SessionLocal() as db:
            slots = await schedule_repo.get_slots(db, doctor_id=doctor_id, target_date=query_date)
            available = [s for s in slots if not s.is_booked]
            if not available:
                return f"No available slots for doctor {doctor_id} on {date}."
            return json.dumps([
                {"slot_id": s.id, "start": s.start_time.strftime("%H:%M"), "end": s.end_time.strftime("%H:%M")}
                for s in available
            ])
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD."
    except Exception as e:
        logger.error(f"get_available_slots error: {e}")
        return f"Error: {str(e)}"


@tool
async def book_appointment(patient_id: int, doctor_id: int, slot_id: int, reason: str) -> str:
    """Book an appointment for a patient. Requires patient_id, doctor_id, slot_id, and reason for visit."""
    try:
        async with SessionLocal() as db:
            appt = await appointment_repo.create_appointment(
                db, patient_id=patient_id, doctor_id=doctor_id, slot_id=slot_id, reason=reason
            )
            return json.dumps({
                "status": "success",
                "appointment_id": appt.id,
                "doctor": appt.doctor.user.full_name,
                "slot": f"{appt.slot.start_time.strftime('%H:%M')} - {appt.slot.end_time.strftime('%H:%M')}"
            })
    except ValueError as e:
        return f"Booking failed: {str(e)}"
    except Exception as e:
        logger.error(f"book_appointment error: {e}")
        return f"Error: {str(e)}"


# ─────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are Aria, a warm and professional AI receptionist for HealthFirst Clinic.

Your personality:
- Friendly, empathetic, and professional
- Concise — responses are optimized for voice, keep them short and natural
- Proactive — guide the patient through the booking process step by step

Your capabilities (use the provided tools):
- list_departments: Check what departments are available
- search_doctors: Find doctors by name or specialization
- get_available_slots: Check available times for a doctor on a specific date
- book_appointment: Finalize a booking

Booking workflow:
1. Ask for preferred specialization or doctor
2. Use search_doctors to find options
3. Ask for preferred date
4. Use get_available_slots to show times
5. Confirm all details with the patient
6. Use book_appointment to finalize

Rules:
- Before calling any tool, say something natural like "Let me check that for you..." or "One moment please..."
- Never show raw IDs to the patient
- The patient_id for this session is injected into your context automatically
- If something fails, apologize and suggest alternatives"""


# ─────────────────────────────────────────────
# ReAct Fallback Prompt (for models without tool support)
# ─────────────────────────────────────────────

REACT_SYSTEM_PROMPT = """You are Aria, a warm AI receptionist for HealthFirst Clinic.

You have access to these tools:
- list_departments(): List all clinic departments
- search_doctors(specialization, name): Find doctors
- get_available_slots(doctor_id, date): Get open slots (date: YYYY-MM-DD)
- book_appointment(patient_id, doctor_id, slot_id, reason): Book appointment

To use a tool, respond EXACTLY in this format:
Thought: I need to check the available doctors.
Action: search_doctors
Action Input: {{"specialization": "Cardiology"}}

After seeing the result, continue with:
Thought: I found the doctors. Now I'll ask the patient.
Final Answer: <your friendly response to the patient>

Rules:
- Always include a Thought before Action or Final Answer
- Keep Final Answer short and voice-friendly
- Use natural filler phrases before actions
- Patient ID: {patient_id}"""


class ClinicAgent:
    def __init__(self, tool_model: str = "llama3.1:8b", fallback_model: str = "llama3"):
        self.tools = [list_departments, search_doctors, get_available_slots, book_appointment]
        self.tool_map = {t.name: t for t in self.tools}

        # Primary: llama3.1 with native tool calling
        try:
            self.llm_with_tools = ChatOllama(model=tool_model, temperature=0.1).bind_tools(self.tools)
            self.tool_model_name = tool_model
            logger.info(f"Agent initialized with native tool support: {tool_model}")
        except Exception as e:
            logger.warning(f"Could not init tool model: {e}")
            self.llm_with_tools = None

        # Fallback: ReAct text-parsing with any model
        self.llm_react = OllamaLLM(model=fallback_model, temperature=0.1)

    async def _run_native_tools(self, user_text: str, patient_id: int) -> str:
        """Use native Ollama tool calling (llama3.1+)."""
        messages = [
            SystemMessage(content=SYSTEM_PROMPT + f"\n\nPatient ID: {patient_id}"),
            HumanMessage(content=user_text),
        ]

        for _ in range(6):
            response = await self.llm_with_tools.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                return response.content or "I'm sorry, could you repeat that?"

            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]
                logger.info(f"Tool call: {tool_name}({tool_args})")

                fn = self.tool_map.get(tool_name)
                result = await fn.ainvoke(tool_args) if fn else f"Unknown tool: {tool_name}"
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_id))

        return "I'm sorry, I couldn't complete that request. Please try again."

    async def _run_react(self, user_text: str, patient_id: int) -> str:
        """Fallback: ReAct text-parsing loop for models without native tool support."""
        system = REACT_SYSTEM_PROMPT.format(patient_id=patient_id)
        history = f"{system}\n\nUser: {user_text}\n"

        for _ in range(6):
            raw = await self.llm_react.ainvoke(history)
            history += raw + "\n"
            logger.info(f"ReAct output: {raw[:200]}")

            # Check for Final Answer
            final_match = re.search(r"Final Answer:\s*(.+)", raw, re.DOTALL)
            if final_match:
                return final_match.group(1).strip()

            # Check for Action + Action Input
            action_match = re.search(r"Action:\s*(\w+)", raw)
            input_match = re.search(r"Action Input:\s*(\{.+?\})", raw, re.DOTALL)

            if action_match and input_match:
                tool_name = action_match.group(1).strip()
                try:
                    tool_args = json.loads(input_match.group(1))
                except json.JSONDecodeError:
                    tool_args = {}

                logger.info(f"ReAct tool call: {tool_name}({tool_args})")
                fn = self.tool_map.get(tool_name)
                result = await fn.ainvoke(tool_args) if fn else f"Unknown tool: {tool_name}"
                history += f"Observation: {result}\n"
            else:
                # No action found, treat the output as a response
                return raw.strip()

        return "I'm sorry, I wasn't able to complete that. Please try again."

    async def get_response(self, user_text: str, patient_id: int = 1) -> str:
        """Route to native tool calling or ReAct fallback."""
        if self.llm_with_tools:
            try:
                return await self._run_native_tools(user_text, patient_id)
            except Exception as e:
                logger.warning(f"Native tool call failed ({e}), falling back to ReAct")

        return await self._run_react(user_text, patient_id)


# Singleton instance
agent = ClinicAgent()
