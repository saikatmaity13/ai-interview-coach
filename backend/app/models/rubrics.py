TECHNICAL_RUBRIC = """
Evaluate the technical answer based on the following dimensions (score 1-5 for each):
1. Correctness: Is the technical information accurate and sound?
2. Depth: Does the candidate show deep understanding rather than superficial knowledge?
3. Clarity: Is the explanation easy to follow and well-structured?
4. Examples: Are practical, relevant examples provided to ground the answer?
"""

BEHAVIORAL_RUBRIC = """
Evaluate the behavioral answer based on the following dimensions (score 1-5 for each):
1. STAR Structure: Did they structure the answer using Situation, Task, Action, Result?
2. Ownership: Did they take responsibility ("I" instead of "we") and show initiative?
3. Quantified Impact: Did they share measurable, objective results?
"""

def get_rubric(category: str) -> str:
    if category.lower() == "behavioral":
        return BEHAVIORAL_RUBRIC
    return TECHNICAL_RUBRIC
