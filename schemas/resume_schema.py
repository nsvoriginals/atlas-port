from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class Location(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

class Experience(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    description: Optional[List[str]] = None

class Project(BaseModel):
    title: str
    description: List[str]

class Education(BaseModel):
    institution: str
    degree: str
    status: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class SkillCategory(BaseModel):
    category: str
    skills: List[str]

class ResumeCreate(BaseModel):
    name: str
    email: str
    phone: str
    location: str
    website: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None
    summary: str
    experience: List[Experience] = []
    projects: List[Project] = []
    education: List[Education] = []
    skills: List[SkillCategory] = []
    awards: List[Dict[str, Any]] = []
    languages: List[Dict[str, Any]] = []
    interests: List[str] = []
    hobbies: List[str] = []
    references: List[Dict[str, Any]] = []

class ResumeResponse(BaseModel):
    id: int
    user_id: int
    template_name: str
    resume_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }