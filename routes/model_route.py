from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from services.model_service import generate_interview_questions

model_router = APIRouter()

class ResumeRequest(BaseModel):
    jobRole: str
    experience: str
    topics: Optional[List[str]] = []
    resumeData: Dict[str, Any]  # Match the exact JSON field name

@model_router.post("/generate")
async def generate_from_json(req: ResumeRequest):
    try:
        print("Received JSON resume data")
        print(f"Job Role: {req.jobRole}, Experience: {req.experience}, Topics: {req.topics}")
        print("Resume basics:", req.resumeData.get("basics", {}))
        
        # You may stringify the resumeData for prompting if needed
        resume_text = json.dumps(req.resumeData, indent=2)
        
        questions = await generate_interview_questions(
            resume_data=req.resumeData,  # not converted to string!
            job_role=req.jobRole,
            experience=req.experience,
            topics=", ".join(req.topics) if req.topics else ""
        )
        
        return {"success": True, "data": questions}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing resume data: {str(e)}")