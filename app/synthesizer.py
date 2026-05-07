import edge_tts
import io
import asyncio

class Synthesizer:
    def __init__(self, voice="en-US-EmmaMultilingualNeural"):
        self.voice = voice

    async def text_to_speech(self, text: str) -> bytes:
        """
        Converts text to speech and returns mp3 bytes.
        """
        communicate = edge_tts.Communicate(text, self.voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

# Singleton instance
synthesizer = Synthesizer()
