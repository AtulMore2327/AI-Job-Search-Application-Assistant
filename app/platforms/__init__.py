"""
Platform adapter registry and factory for multi-platform job discovery.
"""

from typing import Dict, List, Optional
from app.platforms.base_platform import BasePlatformAdapter
from app.platforms.tavily_search import TavilySearchService
from app.platforms.linkedin import LinkedInAdapter
from app.platforms.naukri import NaukriAdapter
from app.platforms.indeed import IndeedAdapter
from app.platforms.internshala import InternshalaAdapter
from app.platforms.foundit import FounditAdapter
from app.platforms.wellfound import WellfoundAdapter
from app.platforms.hirist import HiristAdapter
from app.platforms.glassdoor import GlassdoorAdapter
from app.platforms.shine import ShineAdapter
from app.platforms.timesjobs import TimesJobsAdapter
from app.platforms.cutshort import CutshortAdapter
from app.platforms.apna import ApnaAdapter
from app.platforms.workindia import WorkIndiaAdapter
from app.platforms.company_careers import CompanyCareersAdapter


class PlatformRegistry:
    """Registry managing available platform adapters."""
    
    def __init__(self, search_service: Optional[TavilySearchService] = None):
        self.search_service = search_service or TavilySearchService()
        self._adapters: Dict[str, BasePlatformAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self):
        adapters = [
            LinkedInAdapter(self.search_service),
            NaukriAdapter(self.search_service),
            IndeedAdapter(self.search_service),
            InternshalaAdapter(self.search_service),
            FounditAdapter(self.search_service),
            WellfoundAdapter(self.search_service),
            HiristAdapter(self.search_service),
            GlassdoorAdapter(self.search_service),
            ShineAdapter(self.search_service),
            TimesJobsAdapter(self.search_service),
            CutshortAdapter(self.search_service),
            ApnaAdapter(self.search_service),
            WorkIndiaAdapter(self.search_service),
            CompanyCareersAdapter(self.search_service)
        ]
        for adapter in adapters:
            self._adapters[adapter.platform_name.lower()] = adapter

    def get_adapter(self, platform_name: str) -> Optional[BasePlatformAdapter]:
        """Get platform adapter by name."""
        return self._adapters.get(platform_name.lower())

    def get_all_adapters(self) -> List[BasePlatformAdapter]:
        """Get all registered platform adapters."""
        return list(self._adapters.values())


__all__ = [
    "BasePlatformAdapter",
    "TavilySearchService",
    "PlatformRegistry",
    "LinkedInAdapter",
    "NaukriAdapter",
    "IndeedAdapter",
    "InternshalaAdapter",
    "FounditAdapter",
    "WellfoundAdapter",
    "HiristAdapter",
    "GlassdoorAdapter",
    "ShineAdapter",
    "TimesJobsAdapter",
    "CutshortAdapter",
    "ApnaAdapter",
    "WorkIndiaAdapter",
    "CompanyCareersAdapter"
]
