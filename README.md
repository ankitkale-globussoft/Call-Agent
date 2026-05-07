# Clinic AI Calling Agent Prototype

This is a real-time voice conversation system for a clinic, built with FastAPI, LangChain, Ollama, and Faster-Whisper.

## Tech Stack
- **Backend**: FastAPI (Python 3.10+)
- **LLM**: Ollama (Llama 3)
- **STT**: Faster-Whisper (Base model)
- **TTS**: Edge-TTS (Microsoft Edge Natural Voices)
- **Database**: PostgreSQL (SQLAlchemy Async)
- **Package Manager**: `uv`

## Prerequisites
1. **Ollama**: Install from [ollama.com](https://ollama.com/) and run `ollama run llama3`.
2. **FFmpeg**: Ensure `ffmpeg` is installed on your system and added to your PATH (required for audio processing).
3. **PostgreSQL**: (Optional for first run) The prototype logs to a database. If not available, you can disable the DB logging in `app/main.py`.

## How to Run

1.  **Install dependencies** (already done if you followed the setup):
    ```bash
    uv sync
    ```

2.  **Start the server**:
    ```bash
    uv run uvicorn app.main:app --reload
    ```

3.  **Test the Agent**:
    - Open your browser to `http://localhost:8000/static/index.html`.
    - Click the **Microphone** button.
    - Speak (e.g., "Hi, I'd like to book an appointment for tomorrow morning").
    - Click the button again to stop speaking and send the audio.
    - Wait for the AI to transcribe, think, and reply with voice!

## How it works
1.  **Frontend**: Captures audio using `MediaRecorder` and sends the blob via WebSocket.
2.  **STT**: `faster-whisper` transcribes the audio blob to text.
3.  **LLM**: LangChain sends the text to Ollama (Llama 3) with a specific system prompt for a clinic receptionist.
4.  **TTS**: `edge-tts` converts the AI's text response into high-quality speech.
5.  **Streaming**: The audio response is sent back to the frontend as binary data and played immediately.

## Testing Steps
1.  Verify Ollama is running: `curl http://localhost:11434/api/tags`
2.  Start the FastAPI server.
3.  Open the test page.
4.  Check the terminal logs for transcription and AI response status.
