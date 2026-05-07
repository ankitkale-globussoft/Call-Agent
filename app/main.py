from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
from app.transcriber import transcriber
from app.agent import agent
from app.synthesizer import synthesizer
from app.database import log_call
from app.vad import VADHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Clinic AI Calling Agent")

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    return {"message": "Clinic AI Agent is running. Go to /static/index.html to test."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    # Initialize VAD handler for this session
    # 16kHz, 30ms frames, 1s silence threshold
    vad_handler = VADHandler(sample_rate=16000, frame_duration_ms=30, padding_duration_ms=1000)
    
    try:
        while True:
            # Receive binary chunk from client
            # The client should send raw PCM 16-bit mono 16kHz
            chunk = await websocket.receive_bytes()
            
            if not chunk:
                continue

            # Process chunk through VAD
            is_final, audio_data = vad_handler.process(chunk)

            if is_final:
                logger.info(f"Speech finalized: {len(audio_data)} bytes")
                
                # 1. Transcribe
                user_text = transcriber.transcribe_raw(audio_data)
                logger.info(f"Transcribed Text: {user_text}")

                if user_text:
                    await websocket.send_json({"type": "transcription", "text": user_text})

                    # 2. Agent (LLM)
                    ai_response = await agent.get_response(user_text)
                    logger.info(f"AI Response: {ai_response}")
                    await websocket.send_json({"type": "response", "text": ai_response})

                    # 3. Synthesizer (TTS)
                    audio_response = await synthesizer.text_to_speech(ai_response)
                    logger.info(f"Generated TTS: {len(audio_response)} bytes")

                    # 4. Send Audio back
                    await websocket.send_bytes(audio_response)

                    # 5. Log to DB
                    asyncio.create_task(log_call(user_text, ai_response))
                
                # Reset VAD for next utterance
                vad_handler.reset()

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in websocket loop: {e}")
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
