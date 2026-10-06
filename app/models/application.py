from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ApplicationStatus(str, Enum):
    SAVED = "Saved"
    APPLIED = "Applied"
    INTERVIEW = "Interview"
    REJECTED = "Rejected"
    OFFER = "Offer"
    NOT_INTERESTED = "Not Interested"

class GeneratedApplication(BaseModel):
    job_id: str
    job_title: str
    company: str
    cover_letter: str
    email_subject: str
    hr_email_body: str
    linkedin_message: str
    notes: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.now)

class CoverLetter(BaseModel):
    content: str = ""

class EmailDraft(BaseModel):
    subject: str = ""
    body: str = ""

class LinkedInMessage(BaseModel):
    content: str = ""

class ApplicationPackage(BaseModel):
    cover_letter: str = ""
    email_subject: str = ""
    hr_email_body: str = ""
    linkedin_message: str = ""

class ApplicationWriterRequest(BaseModel):
    job_id: str

class ApplicationTrackerItem(BaseModel):
    application_id: str
    job_id: str
    company: str
    job_title: str
    status: ApplicationStatus = ApplicationStatus.SAVED
    applied_date: Optional[str] = None
    follow_up_date: Optional[str] = None
    notes: str = ""
    updated_at: datetime = Field(default_factory=datetime.now)
