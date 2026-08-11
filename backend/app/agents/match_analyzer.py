import json
from typing import List, Dict, Any
from pydantic import BaseModel
from app.core.llm import llm_client

class MatchAnalysisResult(BaseModel):
    match_percentage: int
    matching_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]

def analyze_resume_match(jd: str, resume_text: str) -> Dict[str, Any]:
    prompt = f"""
    You are an expert technical recruiter and resume analyzer.
    Compare the following Job Description (JD) against the Candidate's Resume.
    
    Job Description:
    {jd}
    
    Candidate Resume:
    {resume_text}
    
    Instructions:
    1. Calculate a realistic Match Percentage (0 to 100) based on skills, experience, and requirements.
    2. Identify key skills and qualifications found in BOTH the JD and Resume (`matching_skills`).
    3. Identify important skills, tools, or requirements listed in the JD that are MISSING or weak in the Resume (`missing_skills`).
    4. Provide 2-3 concise, actionable recommendations (`recommendations`) on what topics or projects the candidate should highlight during the interview to address these gaps.
    """
    
    result: MatchAnalysisResult = llm_client.generate_content(prompt, response_schema=MatchAnalysisResult)
    return result.model_dump()
