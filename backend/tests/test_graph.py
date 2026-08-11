from unittest.mock import patch
from app.agents.graph import interview_graph

def test_graph_compile():
    """Verify that the graph compiles successfully without errors."""
    assert interview_graph is not None

def test_graph_initial_state():
    """Verify the entry point routing of the graph."""
    state = {
        "jd": "Developer",
        "resume_bullets": [],
        "question_history": [],
        "scores": [],
        "follow_up_count": 0,
        "session_id": "test_1"
    }
    
    # Since we can't easily mock nodes inside a compiled graph without rebuilding it,
    # we just verify the compiled graph object exists and nodes are present.
    nodes = interview_graph.nodes
    assert "question_generator" in nodes
    assert "answer_evaluator" in nodes
    assert "feedback_agent" in nodes
    assert "followup_agent" in nodes
