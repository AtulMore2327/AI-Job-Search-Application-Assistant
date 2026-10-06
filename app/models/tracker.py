"""
Pydantic schemas for Application Status Tracker and History.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from app.models.application import ApplicationPackage

VALID_STATUSES = ["SAVED", "APPLIED", "INTERVIEWING", "OFFER", "REJECTED", "WITHDRAWN"]


class TrackedApplication(BaseModel):
    """Application record persisted in tracker database."""
    application_id: str = Field(..., description="Unique application tracker ID")
    job_id: str = Field(..., description="Canonical job ID")
    candidate_name: str = Field(..., description="Candidate full name")
    company: str = Field(..., description="Hiring company name")
    job_title: str = Field(..., description="Job title")
    status: str = Field(default="SAVED", description="Status: SAVED, APPLIED, INTERVIEWING, OFFER, REJECTED, WITHDRAWN")
    notes: Optional[str] = Field(default="", description="User notes or updates")
    applied_date: Optional[str] = Field(default=None, description="Date when application was submitted")
    package: ApplicationPackage = Field(..., description="Associated ApplicationPackage deliverables")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO update timestamp")

    @field_validator("status")
    @classmethod
    def check_valid_status(cls, v: str) -> str:
        upper_v = v.upper().strip()
        if upper_v not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(VALID_STATUSES)}")
        return upper_v


class SaveApplicationRequest(BaseModel):
    """Payload to save an application package to the status tracker."""
    package: ApplicationPackage
    status: str = Field(default="SAVED", description="Initial status")
    notes: Optional[str] = Field(default="", description="Initial notes")
    applied_date: Optional[str] = Field(default=None, description="Applied date if already submitted")


class UpdateStatusRequest(BaseModel):
    """Payload to update an application's status or notes."""
    status: str = Field(..., description="New status")
    notes: Optional[str] = Field(default=None, description="Updated notes")
    applied_date: Optional[str] = Field(default=None, description="Applied date ISO string")


class TrackerStats(BaseModel):
    """Aggregated application tracking statistics."""
    total_applications: int = Field(default=0)
    saved_count: int = Field(default=0)
    applied_count: int = Field(default=0)
    interviewing_count: int = Field(default=0)
    offer_count: int = Field(default=0)
    rejected_count: int = Field(default=0)
    withdrawn_count: int = Field(default=0)
    status_breakdown: Dict[str, int] = Field(default_factory=dict)
