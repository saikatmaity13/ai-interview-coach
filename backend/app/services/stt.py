import numpy as np
from faster_whisper import WhisperModel
import tempfile
import wave
import os

model = WhisperModel("base.en", device="cpu", compute_type="int8")

def is_speech(audio_chunk: bytes, threshold=500) -> bool:
    """
    Simple RMS energy based VAD.
    Assumes 16-bit PCM audio.
    """
    if not audio_chunk:
        return False
    audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
    rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
    return rms > threshold

def transcribe_audio(audio_data: bytes) -> str:
    """
    Transcribes PCM audio bytes using faster-whisper.
    """
    if not audio_data:
        return ""
        
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            with wave.open(temp_wav, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data)
            temp_wav_path = temp_wav.name
            
        segments, info = model.transcribe(temp_wav_path, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        
        os.remove(temp_wav_path)
        return text.strip()
    except Exception as e:
        print(f"Error transcribing: {e}")
        return ""
