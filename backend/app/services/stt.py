import os
import tempfile
import io
from dotenv import load_dotenv

load_dotenv()

def transcribe_audio(audio_data: bytes) -> str:
    """
    Transcribes audio bytes (WAV, WebM, MP3, OGG) using Groq's ultra-fast Whisper API,
    with fallback to local faster-whisper.
    """
    if not audio_data:
        return ""

    # Primary: Groq Cloud Whisper API (Ultra-fast 0.2s, zero memory load)
    api_key = os.environ.get("GROK_API_KEY") or os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            
            # Detect extension or default to wav
            ext = ".wav"
            if audio_data.startswith(b"\x1a\x45\xdf\xa3"):
                ext = ".webm"
            elif audio_data.startswith(b"OggS"):
                ext = ".ogg"

            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"recorded_answer{ext}"

            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file
            )
            return transcription.text.strip()
        except Exception as e:
            print(f"Groq Whisper API Fallback Error: {e}")

    # Secondary Fallback: Local faster-whisper
    try:
        from faster_whisper import WhisperModel
        ext = ".wav"
        if audio_data.startswith(b"\x1a\x45\xdf\xa3"):
            ext = ".webm"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        model = WhisperModel("base.en", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(temp_path, beam_size=3)
        text = " ".join([s.text for s in segments])

        os.remove(temp_path)
        return text.strip()
    except Exception as e:
        print(f"Local Whisper Error: {e}")
        return ""
