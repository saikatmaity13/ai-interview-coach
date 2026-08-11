from typing import TypedDict, List, Dict, Any, Optional

class InterviewState(TypedDict, total=False):
    jd: str
    resume_bullets: List[str]
    role_category: str
    question_history: List[Dict[str, Any]]   # {question, category, difficulty}
    current_question: Dict[str, Any]
    transcript: str
    scores: List[Dict[str, Any]]             # per-question rubric scores
    follow_up_count: int
    session_id: str
    jd_skill_buckets: Optional[Dict[str, Any]]
    feedback_live: str
    feedback_review: str
    current_evaluation: Dict[str, Any]
