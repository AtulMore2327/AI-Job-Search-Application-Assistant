from abc import ABC, abstractmethod
from typing import List
from app.models.job import JobSource, JobSearchPreferences

class BasePlatformAdapter(ABC):
    """Abstract Base Class for Job Platform Adapters."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        pass

    @abstractmethod
    def search_jobs(self, query: str, prefs: JobSearchPreferences) -> List[JobSource]:
        """Search job postings and return raw discovered sources."""
        pass
