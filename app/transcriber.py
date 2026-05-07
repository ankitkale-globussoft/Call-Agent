import io
import numpy as np
from faster_whisper import WhisperModel

class Transcriber:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        # For prototype, cpu is safer. Use "cuda" if GPU is available.
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribes audio bytes to text.
        """
        audio_file = io.BytesIO(audio_data)
        segments, info = self.model.transcribe(audio_file, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()

    def transcribe_raw(self, pcm_data: bytes) -> str:
        """
        Transcribes raw PCM 16-bit mono audio at 16kHz.
        """
        # Convert buffer to float32 numpy array
        audio_np = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(audio_np, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()

# Singleton instance
transcriber = Transcriber()
