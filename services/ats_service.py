# THIS SERVICE HANDLES ATS (APPLICANT TRACKING SYSTEM) ANALYSIS USING GROQ API
from groq import Groq
import os
from typing import Dict, Any
import json
from fastapi import HTTPException

# INITIALIZE GROQ CLIENT
groq_client = Groq(api_key=os.getenv("GROQ_API"))

# MAIN FUNCTION TO ANALYZE RESUME AGAINST JOB DESCRIPTION
async def ats_metrics(resume_data: str, job_description: str) -> Dict[str, Any]:
    """
    Analyze resume against job description using Groq API.
    Returns ATS metrics including score, improvements, summary, and missing keywords.
    """
    prompt = f"""
    You are an expert ATS tracker. Be honest and blunt in your assessment.
    Analyze this resume against the job description and provide:
    1. ATS score (0-100)
    2. Suggested improvements
    3. Resume summary
    4. Missing keywords
    
    Resume Data:
    {json.dumps(resume_data, indent=2)}
    
    Job Description:
    {job_description}
    
    Return response in this JSON format:
    {{
        "ats_score": 0-100,
        "improvements": ["list", "of", "suggestions"],
        "resume_summary": "summary text",
        "missing_keywords": ["list", "of", "keywords"]
    }}
    """
    
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert ATS analyzer."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192",
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ATS analysis failed: {str(e)}"
        )