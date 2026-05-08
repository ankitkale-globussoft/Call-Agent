from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from app.core.config import settings
from app.api.v1.router import api_router
from app.voice.transcriber import transcriber
from app.voice.agent import agent
from app.voice.synthesizer import synthesizer
from app.voice.vad import VADHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"FATAL ERROR: {exc}", exc_info=True)
    return {"detail": "Internal Server Error", "error_type": type(exc).__name__, "message": str(exc)}

@app.get("/health")
async def health():
    return {"status": "ok", "db_url": settings.DATABASE_URL[:20] + "..."}

@app.get("/")
async def root():
    return {"message": "Clinic AI Assistant API is running."}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    vad_handler = VADHandler(sample_rate=16000, frame_duration_ms=30, padding_duration_ms=1000)
    
    try:
        while True:
            chunk = await websocket.receive_bytes()
            if not chunk:
                continue

            is_final, audio_data = vad_handler.process(chunk)

            if is_final:
                user_text = transcriber.transcribe_raw(audio_data)
                if user_text:
                    await websocket.send_json({"type": "transcription", "text": user_text})
                    ai_response = await agent.get_response(user_text)
                    await websocket.send_json({"type": "response", "text": ai_response})
                    audio_response = await synthesizer.text_to_speech(ai_response)
                    await websocket.send_bytes(audio_response)
                vad_handler.reset()

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}", exc_info=True)
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
