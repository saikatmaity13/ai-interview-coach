from langgraph.graph import StateGraph, END
from app.agents.state import InterviewState
from app.agents.question_generator import question_generator
from app.agents.answer_evaluator import answer_evaluator
from app.agents.feedback_agent import feedback_agent
from app.agents.followup_agent import followup_agent

def should_followup(state: InterviewState):
    evaluation = state.get("current_evaluation", {})
    count = state.get("follow_up_count", 0)
    if evaluation.get("needs_followup") and count < 2:
        return "followup_agent"
    return "feedback_agent"

def should_continue(state: InterviewState):
    history = state.get("question_history", [])
    max_q = 8
    if len(history) >= max_q:
        return END
    return "question_generator"

def entry_router(state: InterviewState):
    if not state.get("current_question"):
        return "question_generator"
    else:
        return "answer_evaluator"

def build_graph():
    workflow = StateGraph(InterviewState)
    
    workflow.add_node("question_generator", question_generator)
    workflow.add_node("answer_evaluator", answer_evaluator)
    workflow.add_node("feedback_agent", feedback_agent)
    workflow.add_node("followup_agent", followup_agent)
    
    workflow.set_conditional_entry_point(
        entry_router,
        {
            "question_generator": "question_generator",
            "answer_evaluator": "answer_evaluator"
        }
    )
    
    workflow.add_conditional_edges(
        "answer_evaluator",
        should_followup,
        {
            "followup_agent": "followup_agent",
            "feedback_agent": "feedback_agent"
        }
    )
    
    workflow.add_edge("followup_agent", END)
    
    workflow.add_conditional_edges(
        "feedback_agent",
        should_continue,
        {
            "question_generator": "question_generator",
            END: END
        }
    )
    
    workflow.add_edge("question_generator", END)
    
    return workflow.compile()

interview_graph = build_graph()
