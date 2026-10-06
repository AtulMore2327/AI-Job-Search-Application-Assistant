"""
User Search Preferences and Search Query Pydantic models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class UserPreferences(BaseModel):
    """User search preferences and target criteria."""
    target_role: str = Field(..., description="Target job title or role (e.g., Data Analyst)")
    location: str = Field(default="Any", description="Target location or city (e.g., Surat, Remote)")
    experience_level: str = Field(default="Fresher", description="Fresher, Entry-Level, Mid-Level, Senior")
    employment_type: str = Field(default="Full-time", description="Full-time, Internship, Part-time, Contract")
    work_mode: str = Field(default="Any", description="Onsite, Hybrid, Remote, Any")
    preferred_companies: List[str] = Field(default_factory=list, description="List of preferred target companies")
    skills: List[str] = Field(default_factory=list, description="Key candidate skills to prioritize")
    salary_min: Optional[int] = Field(default=None, ge=0, description="Minimum expected annual salary")
    salary_max: Optional[int] = Field(default=None, ge=0, description="Maximum expected annual salary")
    search_freshness: str = Field(default="30d", description="Freshness window: 24h, 7d, 14d, 30d, any")
    result_limit: int = Field(default=50, ge=1, le=200, description="Maximum number of search results")

    @field_validator("target_role")
    @classmethod
    def check_target_role_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("target_role cannot be empty.")
        return v.strip()

    @field_validator("salary_max")
    @classmethod
    def check_salary_range(cls, v: Optional[int], info) -> Optional[int]:
        salary_min = info.data.get("salary_min")
        if v is not None and salary_min is not None and v < salary_min:
            raise ValueError("salary_max cannot be less than salary_min.")
        return v


class SearchQuery(BaseModel):
    """A generated search query tailored for discovery."""
    query_string: str = Field(..., description="Constructed search query text")
    platform: str = Field(default="General", description="Target platform or engine (e.g., LinkedIn, Naukri, Tavily)")
    query_type: str = Field(default="Role", description="Query strategy type (Role, Boolean, Site-Restricted, Skill-Focused)")
    description: str = Field(..., description="Explanation of query target and purpose")
