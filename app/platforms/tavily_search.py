"""
Tavily Search API Provider Integration.
Executes web discovery queries via Tavily API with retry handling and result normalization.
"""

from typing import List, Optional, Dict, Any
from tavily import TavilyClient

from app.config import get_settings
from app.models.job import RawSearchResult
from app.utils.urls import normalize_url, detect_platform_from_url
from app.utils.retry import retry_with_backoff
from app.utils.logging import get_logger

logger = get_logger("tavily_search")


class TavilySearchService:
    """Service wrapper for Tavily Web Discovery API."""
    
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = settings.TAVILY_API_KEY if api_key is None else api_key
        
        if not self.api_key or self.api_key.startswith("your_") or not self.api_key.strip():
            logger.warning("TAVILY_API_KEY is missing or unconfigured.")
            self.client = None
        else:
            self.client = TavilyClient(api_key=self.api_key)

    def _ensure_client(self) -> TavilyClient:
        """Ensure Tavily client is configured, otherwise raise clear configuration error."""
        if not self.client:
            raise ValueError("Please configure TAVILY_API_KEY to search real jobs. (TAVILY_API_KEY is not configured in settings or .env file.)")
        return self.client

    @retry_with_backoff(retries=2, backoff_in_seconds=0.5, exceptions=(Exception,))
    def execute_search(
        self,
        query_string: str,
        max_results: int = 10,
        include_domains: Optional[List[str]] = None,
        target_platform: str = "General"
    ) -> List[RawSearchResult]:
        """
        Execute search query using Tavily API and return normalized RawSearchResult objects.
        
        Args:
            query_string: Search text string.
            max_results: Maximum number of search results to return.
            include_domains: Optional list of domains to filter by.
            target_platform: Expected platform name or 'General'.
            
        Returns:
            List of normalized RawSearchResult objects.
        """
        client = self._ensure_client()
        logger.info(f"Executing Tavily search for query: '{query_string}' (target: {target_platform})")
        
        search_kwargs: Dict[str, Any] = {
            "query": query_string,
            "max_results": max_results,
            "search_depth": "basic"
        }
        
        if include_domains:
            search_kwargs["include_domains"] = include_domains
            
        response = client.search(**search_kwargs)
        results: List[RawSearchResult] = []
        
        raw_results = response.get("results", [])
        for item in raw_results:
            raw_url = item.get("url", "")
            if not raw_url:
                continue
                
            clean_url = normalize_url(raw_url)
            detected = detect_platform_from_url(clean_url)
            
            # Use detected platform if specific, else fallback to target_platform
            platform_name = detected if detected not in ["Other", "Unknown"] else target_platform
            
            result = RawSearchResult(
                title=item.get("title", "Untitled Job"),
                url=clean_url,
                platform=platform_name,
                snippet=item.get("content", item.get("snippet", "")),
                score=item.get("score"),
                query=query_string,
                raw_data=item
            )
            results.append(result)
            
        logger.info(f"Tavily returned {len(results)} results for query: '{query_string}'")
        return results
