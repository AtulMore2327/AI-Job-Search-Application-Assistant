"""
Cutshort Platform Adapter.
"""

from typing import List, Optional
from app.platforms.base_platform import BasePlatformAdapter
from app.platforms.tavily_search import TavilySearchService
from app.models.preferences import SearchQuery
from app.models.job import RawSearchResult

class CutshortAdapter(BasePlatformAdapter):
    """Adapter for searching Cutshort tech job listings via Tavily web discovery."""
    
    def __init__(self, search_service: Optional[TavilySearchService] = None):
        super().__init__(platform_name="Cutshort", domains=["cutshort.io"])
        self.search_service = search_service or TavilySearchService()

    def search(self, query: SearchQuery, limit: int = 10) -> List[RawSearchResult]:
        return self.search_service.execute_search(
            query_string=query.query_string,
            max_results=limit,
            include_domains=self.domains,
            target_platform=self.platform_name
        )
