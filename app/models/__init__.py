"""
Data models and schemas for candidate, job, preferences, application, and matching.
"""

from app.models.candidate import CandidateProfile, EducationItem, ExperienceItem, ProjectItem
from app.models.preferences import UserPreferences, SearchQuery
from app.models.job import RawSearchResult, DiscoveryResult, URLClassificationResult, Job, JDAnalysis, JDExtractResult
from app.models.matching import (
    PreferenceCheck,
    PreferenceFilterResult,
    SkillMatch,
    SkillGap,
    MatchResult,
    FilterJobRequest,
    MatchJobRequest,
    SkillGapRequest,
    BatchMatchJobRequest
)
from app.models.application import (
    CoverLetter,
    EmailDraft,
    LinkedInMessage,
    ApplicationPackage,
    ApplicationWriterRequest
)
from app.models.tracker import (
    TrackedApplication,
    SaveApplicationRequest,
    UpdateStatusRequest,
    TrackerStats
)

__all__ = [
    "CandidateProfile",
    "EducationItem",
    "ExperienceItem",
    "ProjectItem",
    "UserPreferences",
    "SearchQuery",
    "RawSearchResult",
    "DiscoveryResult",
    "URLClassificationResult",
    "Job",
    "JDAnalysis",
    "JDExtractResult",
    "PreferenceCheck",
    "PreferenceFilterResult",
    "SkillMatch",
    "SkillGap",
    "MatchResult",
    "FilterJobRequest",
    "MatchJobRequest",
    "SkillGapRequest",
    "BatchMatchJobRequest",
    "CoverLetter",
    "EmailDraft",
    "LinkedInMessage",
    "ApplicationPackage",
    "ApplicationWriterRequest",
    "TrackedApplication",
    "SaveApplicationRequest",
    "UpdateStatusRequest",
    "TrackerStats"
]
