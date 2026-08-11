import os
import io
from dotenv import load_dotenv

load_dotenv()

TTS_ENABLED = os.environ.get("TTS_ENABLED", "true").lower() == "true"
PIPER_MODEL_PATH = os.environ.get("PIPER_MODEL_PATH", "en_US-lessac-medium.onnx")

def generate_audio(text: str) -> bytes:
    if not TTS_ENABLED or not text or not text.strip():
        return b""
        
    # Attempt Piper TTS first if local model exists
    if os.path.exists(PIPER_MODEL_PATH):
        try:
            import tempfile, wave
            from piper import PiperVoice
            voice = PiperVoice.load(PIPER_MODEL_PATH)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                with wave.open(temp_wav.name, 'wb') as wf:
                    voice.synthesize(text, wf)
                temp_wav_path = temp_wav.name
            with open(temp_wav_path, "rb") as f:
                audio_bytes = f.read()
            os.remove(temp_wav_path)
            return audio_bytes
        except Exception as e:
            print(f"Piper TTS fallback to gTTS: {e}")

    # Primary reliable fallback: gTTS
    try:
        from gtts import gTTS
        mp3_fp = io.BytesIO()
        tts = gTTS(text=text, lang='en', slow=False)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp.read()
    except Exception as e:
        print(f"gTTS Error: {e}")
        return b""
