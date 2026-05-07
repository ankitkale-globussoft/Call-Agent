import webrtcvad
import collections

class VADHandler:
    def __init__(self, sample_rate=16000, frame_duration_ms=30, padding_duration_ms=1000):
        self.vad = webrtcvad.Vad(3)  # Aggressiveness 3 (highest)
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000) * 2 # 2 bytes per sample (16-bit)
        
        self.padding_duration_ms = padding_duration_ms
        self.num_padding_frames = int(padding_duration_ms / frame_duration_ms)
        self.ring_buffer = collections.deque(maxlen=self.num_padding_frames)
        
        self.triggered = False
        self.voiced_frames = []
        self.audio_buffer = bytearray()

    def is_speech(self, frame):
        """Returns True if the frame contains speech."""
        return self.vad.is_speech(frame, self.sample_rate)

    def process(self, chunk):
        """
        Processes a chunk of raw PCM 16-bit audio.
        Returns a tuple (is_final, audio_data).
        is_final: True if speech has finished after a silence.
        audio_data: The accumulated audio if finalized, else None.
        """
        self.audio_buffer.extend(chunk)
        
        # We need to process in fixed frame sizes (e.g. 30ms)
        while len(self.audio_buffer) >= self.frame_size:
            frame = bytes(self.audio_buffer[:self.frame_size])
            del self.audio_buffer[:self.frame_size]
            
            is_speech = self.is_speech(frame)
            
            if not self.triggered:
                self.ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in self.ring_buffer if speech])
                if num_voiced > 0.9 * self.ring_buffer.maxlen:
                    self.triggered = True
                    for f, s in self.ring_buffer:
                        self.voiced_frames.append(f)
                    self.ring_buffer.clear()
            else:
                self.voiced_frames.append(frame)
                self.ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in self.ring_buffer if not speech])
                if num_unvoiced > 0.9 * self.ring_buffer.maxlen:
                    self.triggered = False
                    final_audio = b"".join(self.voiced_frames)
                    self.voiced_frames = []
                    self.ring_buffer.clear()
                    return True, final_audio
                    
        return False, None

    def reset(self):
        self.triggered = False
        self.voiced_frames = []
        self.audio_buffer = bytearray()
        self.ring_buffer.clear()
