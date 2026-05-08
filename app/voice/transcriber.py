import io
import numpy as np
from faster_whisper import WhisperModel
import logging

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Loading Whisper model: {self.model_size}...")
            self._model = WhisperModel(
                self.model_size, 
                device=self.device, 
                compute_type=self.compute_type
            )
            logger.info("Whisper model loaded successfully.")
        return self._model

    def transcribe(self, audio_data: bytes) -> str:
        audio_file = io.BytesIO(audio_data)
        segments, info = self.model.transcribe(audio_file, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()

    def transcribe_raw(self, pcm_data: bytes) -> str:
        # Convert buffer to float32 numpy array
        audio_np = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(audio_np, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()

# Singleton instance
transcriber = Transcriber()
