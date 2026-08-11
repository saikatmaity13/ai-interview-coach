import json
from typing import Dict, Any
from pydantic import BaseModel
from app.agents.state import InterviewState
from app.core.llm import llm_client

class FeedbackOutput(BaseModel):
    live_feedback: str
    review_feedback: str

def feedback_agent(state: InterviewState) -> Dict[str, Any]:
    evaluation = state.get("current_evaluation", {})
    
    prompt = f"""
    Based on the following evaluation of the candidate's answer, generate two types of feedback:
    1. 'live_feedback': A terse, 1-2 sentence encouraging response that will be spoken via TTS before moving to the next question.
    2. 'review_feedback': A full written breakdown for the post-interview dashboard.
    
    Evaluation:
    {json.dumps(evaluation, indent=2)}
    """
    
    result: FeedbackOutput = llm_client.generate_content(prompt, response_schema=FeedbackOutput)
    
    new_history = state.get("question_history", []) + [state.get("current_question")]
    
    # Update the latest score review with review_feedback if available
    scores = list(state.get("scores", []))
    if scores:
        scores[-1]["review"] = result.review_feedback
        
    return {
        "feedback_live": result.live_feedback,
        "feedback_review": result.review_feedback,
        "scores": scores,
        "question_history": new_history
    }
