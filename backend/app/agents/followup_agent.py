import json
from typing import Dict, Any
from pydantic import BaseModel
from app.agents.state import InterviewState
from app.core.llm import llm_client

class FollowUpOutput(BaseModel):
    question: str
    live_feedback: str

def followup_agent(state: InterviewState) -> Dict[str, Any]:
    question = state.get("current_question", {})
    evaluation = state.get("current_evaluation", {})
    count = state.get("follow_up_count", 0)
    
    prompt = f"""
    The candidate provided an answer that needs a follow-up to dig deeper or address missing points.
    
    Original Question: {question.get('question')}
    Candidate Answer: {state.get('transcript')}
    Evaluation: {json.dumps(evaluation, indent=2)}
    
    Instructions:
    Generate a probing follow-up question to dig deeper into the weak areas identified in the evaluation.
    Also generate a brief 'live_feedback' (1 sentence) to be spoken before the question, e.g., "Good point, but could you elaborate on..."
    """
    
    result: FollowUpOutput = llm_client.generate_content(prompt, response_schema=FollowUpOutput)
    
    new_question = {
        "question": result.question,
        "category": question.get("category"),
        "difficulty": question.get("difficulty"),
        "ideal_answer_keywords": question.get("ideal_answer_keywords")
    }
    
    return {
        "current_question": new_question,
        "follow_up_count": count + 1,
        "transcript": "",
        "feedback_live": result.live_feedback + " " + result.question
    }
