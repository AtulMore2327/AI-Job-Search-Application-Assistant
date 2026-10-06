from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class SkillGapAnalysis(BaseModel):
    matched_skills: List[str] = Field(default_factory=list)
    partially_matched_skills: List[str] = Field(default_factory=list)
    missing_must_have: List[str] = Field(default_factory=list)
    missing_nice_to_have: List[str] = Field(default_factory=list)
    not_evidenced: List[str] = Field(default_factory=list)

SkillGap = SkillGapAnalysis

class MatchScoreBreakdown(BaseModel):
    skills_score: float = 0.0          # Max 45
    experience_score: float = 0.0      # Max 20
    education_score: float = 0.0       # Max 10
    responsibilities_score: float = 0.0 # Max 15
    keywords_score: float = 0.0        # Max 10

class JobMatchResult(BaseModel):
    job_id: str
    job_title: str
    company: str
    match_score: float                  # 0 to 100 deterministic percentage
    breakdown: MatchScoreBreakdown
    skill_gap: SkillGapAnalysis
    explanation: str = ""
    is_preference_match: bool = True
    preference_reasons: List[str] = Field(default_factory=list)

MatchResult = JobMatchResult

class PreferenceCheck(BaseModel):
    criterion: str = ""
    passed: bool = True
    status: str = "passed"
    reason: str = ""

class PreferenceFilterResult(BaseModel):
    job_id: str
    passed: bool = True
    is_match: bool = True
    failed_criteria: List[str] = Field(default_factory=list)
    checks: List[PreferenceCheck] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)

class SkillMatch(BaseModel):
    skill: str
    status: str

class FilterJobRequest(BaseModel):
    job_id: str

class MatchJobRequest(BaseModel):
    job_id: str

class SkillGapRequest(BaseModel):
    job_id: str

class BatchMatchJobRequest(BaseModel):
    job_ids: List[str] = Field(default_factory=list)
