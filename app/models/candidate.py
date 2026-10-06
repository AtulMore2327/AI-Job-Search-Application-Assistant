from pydantic import BaseModel, Field
from typing import List, Optional

class EducationItem(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None
    details: Optional[str] = None

class ProjectItem(BaseModel):
    title: str
    description: str
    technologies: List[str] = Field(default_factory=list)

class ExperienceItem(BaseModel):
    role: str
    company: str
    duration: Optional[str] = None
    description: Optional[str] = None

class CandidateProfile(BaseModel):
    name: str = "Candidate"
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    target_role: Optional[str] = None
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    summary: str = ""
    keywords: List[str] = Field(default_factory=list)
    raw_text: str = ""
