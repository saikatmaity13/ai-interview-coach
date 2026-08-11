# AI Interview Coach

A multi-agent, voice-enabled mock interview system powered by LangGraph, FastAPI, Streamlit, and local STT/TTS.

## Architecture
The system consists of a FastAPI backend managing a LangGraph StateGraph, and a Streamlit frontend for the user interface. 

- **Backend**: FastAPI, WebSocket for streaming audio.
- **Orchestration**: LangGraph state machine with Gemini 2.5 Flash via `google-generativeai`.
- **STT**: Local `faster-whisper` for fast transcriptions.
- **TTS**: Local `piper-tts` (optional via `.env`).
- **Database**: SQLite using SQLAlchemy (stores sessions, questions, transcripts, and scores).
- **Frontend**: Streamlit app with built-in audio input for mic recording and Plotly for the post-session dashboard.

## Setup

1. **Environment Variables**
   Copy `.env.example` to `.env` and fill in your Gemini API key:
   ```bash
   cp .env.example .env
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Piper TTS and Faster-Whisper might require additional system dependencies depending on your OS)*

3. **Run the Backend**
   Ensure you are in the `backend` directory:
   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Run the Frontend**
   In a separate terminal, from the root directory:
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

## CLI Testing
You can also run a text-only test of the agent graph without starting the servers:
```bash
python cli_test.py
```
