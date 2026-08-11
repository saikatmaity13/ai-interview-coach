import json
from typing import Dict, Any, List
from pydantic import BaseModel
from app.agents.state import InterviewState
from app.core.llm import llm_client
from app.models.rubrics import get_rubric

class DimensionScore(BaseModel):
    dimension: str
    score: int
    justification: str

class EvaluatorOutput(BaseModel):
    scores: List[DimensionScore]
    needs_followup: bool
    overall_feedback: str

def answer_evaluator(state: InterviewState) -> Dict[str, Any]:
    question = state.get("current_question", {})
    transcript = state.get("transcript", "")
    category = question.get("category", "technical")
    
    rubric = get_rubric(category)
    
    prompt = f"""
    You are an expert interviewer evaluating a candidate's answer.
    
    Question: {question.get('question')}
    Category: {category}
    Ideal Keywords: {', '.join(question.get('ideal_answer_keywords', []))}
    
    Rubric:
    {rubric}
    
    Candidate's Transcript:
    {transcript}
    
    Instructions:
    - Evaluate the transcript against each dimension in the rubric.
    - Provide a score from 1-5 and a short justification for each dimension.
    - Determine if a follow-up question is needed (`needs_followup`). If the answer is incomplete, too brief, or misses key components, set this to true.
    - Be strict. Avoid score inflation.
    
    Few-shot Example (Technical):
    Weak Answer (Score 1-2): "I just used React for the frontend and it worked fine." (Lacks depth, no examples, poor clarity).
    Strong Answer (Score 4-5): "I chose React because of its virtual DOM for performance. I implemented custom hooks to manage state, reducing re-renders by 30%, as seen in the dashboard component." (Clear, deep, concrete examples).
    """
    
    result: EvaluatorOutput = llm_client.generate_content(prompt, response_schema=EvaluatorOutput)
    
    new_score = {
        "question": question,
        "evaluation": result.model_dump(),
        "review": result.overall_feedback
    }
    
    scores = state.get("scores", []) + [new_score]
    
    return {
        "current_evaluation": result.model_dump(),
        "scores": scores
    }
