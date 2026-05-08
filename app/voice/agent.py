from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class ClinicAgent:
    def __init__(self, model_name="llama3"):
        self.llm = OllamaLLM(model=model_name)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful and professional AI receptionist for 'HealthFirst Clinic'.
Your goal is to assist patients with booking appointments, answering basic clinic questions (hours: 9 AM - 6 PM), and being polite.
Keep your responses concise and natural for a voice conversation. Avoid long lists.
Current context: Booking appointments, clinic info."""),
            ("user", "{input}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def get_response(self, user_text: str) -> str:
        """
        Generates a response from the LLM.
        """
        response = await self.chain.ainvoke({"input": user_text})
        return response

# Singleton instance
agent = ClinicAgent()
