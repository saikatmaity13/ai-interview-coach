import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add backend to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.agents.graph import interview_graph

def run_cli_test():
    print("Starting AI Interview Coach CLI Test...")
    
    jd = """
    We are looking for a Senior Python Developer.
    Requirements:
    - 5+ years of experience with Python and FastAPI.
    - Strong understanding of microservices architecture.
    - Experience with SQL databases (PostgreSQL) and SQLAlchemy.
    - Excellent communication skills.
    """
    
    resume_bullets = [
        "Built a high-performance REST API using FastAPI serving 1M requests/day.",
        "Migrated legacy monolithic application to microservices on AWS.",
        "Optimized SQL queries reducing latency by 40%."
    ]
    
    state = {
        "jd": jd,
        "resume_bullets": resume_bullets,
        "role_category": "Software Engineering",
        "question_history": [],
        "scores": [],
        "follow_up_count": 0,
        "session_id": "cli_test_session"
    }
    
    print("\n--- Generating First Question ---")
    state = interview_graph.invoke(state)
    
    while True:
        question = state.get("current_question", {})
        
        # Print coach's live feedback if any
        if state.get("feedback_live"):
            print(f"\n[Coach]: {state.get('feedback_live')}")
            
        print(f"\n[Category: {question.get('category')} | Difficulty: {question.get('difficulty')}]")
        print(f"Question: {question.get('question')}")
        
        transcript = input("\nYour Answer (type 'quit' to exit): ")
        if transcript.lower() in ['quit', 'exit']:
            break
            
        state["transcript"] = transcript
        
        print("\n--- Evaluating Answer ---")
        state = interview_graph.invoke(state)
        
        # Check if max questions reached (default 8)
        if len(state.get("question_history", [])) >= 8:
            print("\nInterview Complete! Summary:")
            for score in state.get("scores", []):
                print(f"\nQ: {score['question']['question']}")
                print(f"Review: {score['review']}")
            break

if __name__ == "__main__":
    run_cli_test()
