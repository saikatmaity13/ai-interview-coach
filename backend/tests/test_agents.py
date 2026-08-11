from unittest.mock import patch, MagicMock
from app.agents.state import InterviewState
from app.agents.question_generator import question_generator
from app.agents.answer_evaluator import answer_evaluator

@patch("app.agents.question_generator.llm_client.generate_content")
def test_question_generator(mock_generate):
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {
        "question": "What is Python?",
        "category": "technical",
        "difficulty": "Easy",
        "ideal_answer_keywords": ["language", "programming"]
    }
    mock_generate.return_value = mock_result
    
    state = {
        "jd": "Python dev",
        "resume_bullets": [],
        "jd_skill_buckets": {"technical": ["Python"]}
    }
    
    new_state = question_generator(state)
    assert new_state["current_question"]["question"] == "What is Python?"
    assert new_state["transcript"] == ""
    assert new_state["follow_up_count"] == 0

@patch("app.agents.answer_evaluator.llm_client.generate_content")
def test_answer_evaluator(mock_generate):
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {
        "scores": [{"dimension": "Correctness", "score": 5, "justification": "Good"}],
        "needs_followup": False,
        "overall_feedback": "Great"
    }
    mock_generate.return_value = mock_result
    
    state = {
        "current_question": {"question": "What is Python?", "category": "technical", "ideal_answer_keywords": []},
        "transcript": "It is a language."
    }
    
    new_state = answer_evaluator(state)
    assert "current_evaluation" in new_state
    assert not new_state["current_evaluation"]["needs_followup"]
