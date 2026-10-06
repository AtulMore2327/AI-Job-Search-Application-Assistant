from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PageType(str, Enum):
    INDIVIDUAL_JOB = "INDIVIDUAL_JOB"
    LISTING_PAGE = "LISTING_PAGE"
    COMPANY_PAGE = "COMPANY_PAGE"
    SEARCH_PAGE = "SEARCH_PAGE"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"

class WorkMode(str, Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ONSITE = "On-site"
    ANY = "Any"

class JobSource(BaseModel):
    platform: str
    url: str
    canonical_url: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    score: float = 0.0
    hr_email: Optional[str] = None

RawSearchResult = JobSource

class JobPosting(BaseModel):
    job_id: str
    title: str
    company: str
    location: str = "India"
    work_mode: str = "On-site"
    employment_type: str = "Full-time"
    experience_level: str = "Any"
    salary: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    posted_date: Optional[str] = None
    description: str = ""
    hr_email: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    sources: List[JobSource] = Field(default_factory=list)
    canonical_url: str = ""
    page_type: PageType = PageType.INDIVIDUAL_JOB
    validation_status: str = "VALID"
    extraction_status: str = "COMPLETED"
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

Job = JobPosting

class DiscoveryResult(BaseModel):
    sources: List[JobSource] = Field(default_factory=list)

class JDExtractResult(BaseModel):
    job_id: str
    title: str
    description: str

class JDAnalysis(BaseModel):
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    experience_required: str = ""
    education_required: str = ""
    work_mode: str = ""
    employment_type: str = ""
    important_keywords: List[str] = Field(default_factory=list)

class URLClassificationResult(BaseModel):
    url: str
    page_type: PageType
    confidence: float = 1.0
    reason: str = ""

class JobSearchPreferences(BaseModel):
    target_role: str = "Data Analyst"
    location: str = "Indore"
    experience_level: str = "Fresher"
    employment_type: str = "Full-time"
    work_mode: str = "On-site"
    preferred_companies: List[str] = Field(default_factory=list)
    result_limit: int = 10
    freshness: str = "Anytime"
