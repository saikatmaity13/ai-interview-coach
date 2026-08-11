import sys
import os
# Add the backend directory to sys.path so 'app' module can be resolved regardless of where uvicorn is run from
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
import json

from app.db.database import engine, Base, get_db
from app.db import models
from app.agents.graph import interview_graph
from app.services.stt import transcribe_audio
from app.services.tts import generate_audio
import base64

from app.agents.match_analyzer import analyze_resume_match

from fastapi.middleware.cors import CORSMiddleware

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Interview Coach")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "AI Interview Coach API",
        "docs": "/docs"
    }

class StartSessionRequest(BaseModel):
    jd: str
    resume_text: str
    interview_mode: str = "Full Mock Interview (Mixed)"
    num_questions: int = 8

class MatchRequest(BaseModel):
    jd: str
    resume_text: str

@app.post("/analyze/resume-match")
def analyze_match(request: MatchRequest):
    return analyze_resume_match(request.jd, request.resume_text)

active_sessions = {} # session_id -> graph state dict

def sync_scores_to_db(state, db: Session):
    session_id = state["session_id"]
    for score_data in state.get("scores", []):
        q_data = score_data["question"]
        # Find question
        db_q = db.query(models.Question).filter_by(
            session_id=session_id, question_text=q_data["question"]
        ).first()
        
        if not db_q:
            db_q = models.Question(
                session_id=session_id,
                question_text=q_data["question"],
                category=q_data["category"],
                difficulty=q_data["difficulty"]
            )
            db.add(db_q)
            db.commit()
            db.refresh(db_q)
            
        # Add scores if not already added
        existing_scores = db.query(models.Score).filter_by(question_id=db_q.id).count()
        if existing_scores == 0:
            eval_data = score_data.get("evaluation", {})
            for dim_score in eval_data.get("scores", []):
                db_score = models.Score(
                    question_id=db_q.id,
                    dimension=dim_score["dimension"],
                    score_value=dim_score["score"],
                    justification=dim_score["justification"]
                )
                db.add(db_score)
            db.commit()

@app.post("/session/start")
def start_session(request: StartSessionRequest, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    
    db_session = models.Session(
        id=session_id,
        jd=request.jd,
        resume_text=request.resume_text,
        num_questions=request.num_questions
    )
    db.add(db_session)
    db.commit()
    
    resume_bullets = [b.strip() for b in request.resume_text.split('\n') if b.strip()]
    
    state = {
        "jd": request.jd,
        "resume_bullets": resume_bullets,
        "interview_mode": request.interview_mode,
        "role_category": "General",
        "question_history": [],
        "scores": [],
        "follow_up_count": 0,
        "session_id": session_id
    }
    
    # Generate first question
    state = interview_graph.invoke(state)
    active_sessions[session_id] = state
    
    q = state["current_question"]
    db_q = models.Question(
        session_id=session_id,
        question_text=q["question"],
        category=q["category"],
        difficulty=q["difficulty"]
    )
    db.add(db_q)
    db.commit()
    
    # Generate TTS audio for the first question
    q_audio_bytes = generate_audio(q["question"])
    q_audio_b64 = base64.b64encode(q_audio_bytes).decode('utf-8') if q_audio_bytes else ""
    
    return {
        "session_id": session_id,
        "first_question": q,
        "question_audio": q_audio_b64
    }

def get_or_restore_state(session_id: str, db: Session):
    if session_id in active_sessions:
        return active_sessions[session_id]
        
    db_session = db.query(models.Session).filter_by(id=session_id).first()
    if not db_session:
        return None
        
    resume_bullets = [b.strip() for b in db_session.resume_text.split('\n') if b.strip()]
    db_qs = db.query(models.Question).filter_by(session_id=session_id).all()
    q_history = [{"question": q.question_text, "category": q.category, "difficulty": q.difficulty} for q in db_qs]
    last_q = q_history[-1] if q_history else {}
    
    state = {
        "jd": db_session.jd,
        "resume_bullets": resume_bullets,
        "interview_mode": "Full Mock Interview (Mixed)",
        "role_category": "General",
        "question_history": q_history,
        "current_question": last_q,
        "scores": [],
        "follow_up_count": 0,
        "session_id": session_id
    }
    active_sessions[session_id] = state
    return state

def handle_answer_turn(session_id: str, message: dict, db: Session):
    state = get_or_restore_state(session_id, db)
    if not state:
        return None, {"error": "Session not found"}
        
    if message.get("type") == "answer_text":
        state["transcript"] = message.get("transcript")
    elif message.get("type") == "answer_audio":
        audio_b64 = message.get("audio_data")
        audio_bytes = base64.b64decode(audio_b64)
        transcript = transcribe_audio(audio_bytes)
        state["transcript"] = transcript
        
    # Run graph
    state = interview_graph.invoke(state)
    active_sessions[session_id] = state
    
    sync_scores_to_db(state, db)
    
    feedback_live = state.get("feedback_live")
    feedback_audio_bytes = b""
    if feedback_live:
        feedback_audio_bytes = generate_audio(feedback_live)
        
    next_q = state.get("current_question")
    q_audio_bytes = b""
    if next_q and next_q.get("question"):
        q_audio_bytes = generate_audio(next_q["question"])
        
    response = {
        "type": "next_turn",
        "feedback_live": feedback_live,
        "feedback_audio": base64.b64encode(feedback_audio_bytes).decode('utf-8') if feedback_audio_bytes else "",
        "next_question": next_q,
        "question_audio": base64.b64encode(q_audio_bytes).decode('utf-8') if q_audio_bytes else ""
    }
    
    if len(state.get("question_history", [])) >= 8:
        response["type"] = "end_interview"
        
    return state, response

class AnswerPayload(BaseModel):
    type: str
    transcript: str = None
    audio_data: str = None

@app.post("/session/{session_id}/answer")
def submit_answer_http(session_id: str, payload: AnswerPayload, db: Session = Depends(get_db)):
    state, response = handle_answer_turn(session_id, payload.model_dump(), db)
    if not state:
        return {"error": "Session not found"}
    return response

@app.websocket("/session/{session_id}/answer")
async def websocket_endpoint(websocket: WebSocket, session_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    state = get_or_restore_state(session_id, db)
    if not state:
        await websocket.close(code=1008)
        return
        
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            state, response = handle_answer_turn(session_id, message, db)
            await websocket.send_text(json.dumps(response))
            if response and response.get("type") == "end_interview":
                break
    except WebSocketDisconnect:
        pass
        
@app.get("/session/{session_id}/summary")
def get_summary(session_id: str, db: Session = Depends(get_db)):
    state = active_sessions.get(session_id)
    if state and state.get("scores"):
        return {"scores": state.get("scores")}
        
    # Database Fallback
    db_questions = db.query(models.Question).filter_by(session_id=session_id).all()
    if not db_questions:
        return {"scores": []}
        
    formatted_scores = []
    for q in db_questions:
        if not q.scores:
            continue
        dim_scores = [
            {
                "dimension": s.dimension,
                "score": s.score_value,
                "justification": s.justification
            }
            for s in q.scores
        ]
        formatted_scores.append({
            "question": {
                "question": q.question_text,
                "category": q.category or "General",
                "difficulty": q.difficulty or "Medium"
            },
            "review": f"Evaluated across {len(dim_scores)} core criteria.",
            "evaluation": {
                "scores": dim_scores
            }
        })
        
    return {"scores": formatted_scores}
