import io
import numpy as np
from faster_whisper import WhisperModel
import wave

class Transcriber:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        # For prototype, cpu is safer. Use "cuda" if GPU is available.
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribes audio bytes to text.
        Assumes audio_data is raw PCM or a format supported by faster-whisper.
        For simplicity in this prototype, we'll assume it's a WAV file in memory.
        """
        audio_file = io.BytesIO(audio_data)
        segments, info = self.model.transcribe(audio_file, beam_size=5)
        
        text = " ".join([segment.text for segment in segments])
        return text.strip()

# Singleton instance
transcriber = Transcriber()
