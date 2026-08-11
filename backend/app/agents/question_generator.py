import json
from typing import List, Dict, Any
from pydantic import BaseModel
from app.agents.state import InterviewState
from app.core.llm import llm_client

class JDBuckets(BaseModel):
    technical: List[str]
    behavioral: List[str]
    system_design: List[str]
    role_specific: List[str]

class QuestionOutput(BaseModel):
    question: str
    category: str
    difficulty: str
    ideal_answer_keywords: List[str]

def extract_jd_buckets(jd: str) -> dict:
    prompt = f"Parse the following Job Description into key skill buckets.\n\nJD:\n{jd}"
    result = llm_client.generate_content(prompt, response_schema=JDBuckets)
    return result.model_dump()

def question_generator(state: InterviewState) -> Dict[str, Any]:
    jd_buckets = state.get("jd_skill_buckets")
    if not jd_buckets:
        jd_buckets = extract_jd_buckets(state.get("jd", ""))
    
    interview_mode = state.get("interview_mode", "Full Mock Interview (Mixed)")
    question_history = state.get("question_history", [])
    past_questions = [q["question"] for q in question_history]
    
    mode_instructions = ""
    if interview_mode == "Coding & Technical Deep-Dive":
        mode_instructions = "MUST focus strictly on technical coding algorithms, data structures, framework internals, and language-specific optimizations. Category MUST be 'technical'."
    elif interview_mode == "Behavioral (STAR Method Focus)":
        mode_instructions = "MUST focus strictly on past workplace scenarios, leadership, conflict resolution, and communication using the STAR framework (Situation, Task, Action, Result). Category MUST be 'behavioral'."
    elif interview_mode == "System Design & Architecture":
        mode_instructions = "MUST focus strictly on high-level system architecture, distributed systems, database scaling, API design, caching, and infrastructure. Category MUST be 'system_design'."
    else:
        mode_instructions = "Mix technical, behavioral, system design, and resume project deep-dives balanced across the interview."
    
    prompt = f"""
    You are an expert interviewer. Generate the next interview question for this candidate.
    
    Interview Mode: {interview_mode}
    Mode Focus: {mode_instructions}
    
    Job Description Skill Buckets:
    {json.dumps(jd_buckets, indent=2)}
    
    Candidate Resume Project Bullets:
    {json.dumps(state.get("resume_bullets", []), indent=2)}
    
    Past Questions Asked:
    {json.dumps(past_questions, indent=2)}
    
    Instructions:
    - Adhere strictly to the Mode Focus above.
    - Never repeat a question already in Past Questions Asked.
    - Return a structured output with the question, category (technical, behavioral, system_design, or role_specific), difficulty (Easy, Medium, Hard), and ideal_answer_keywords.
    """
    
    result: QuestionOutput = llm_client.generate_content(prompt, response_schema=QuestionOutput)
    
    return {
        "jd_skill_buckets": jd_buckets,
        "current_question": result.model_dump(),
        "transcript": "", # Reset transcript for new question
        "follow_up_count": 0
    }
