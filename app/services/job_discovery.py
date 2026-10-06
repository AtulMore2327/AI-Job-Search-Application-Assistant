"""
Multi-platform job discovery orchestrator.
Executes queries across platform adapters and aggregates normalized RawSearchResult objects.
"""

from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timezone

from app.config import get_settings
from app.models.preferences import SearchQuery
from app.models.job import RawSearchResult, DiscoveryResult
from app.platforms import PlatformRegistry, TavilySearchService
from app.utils.logging import get_logger

logger = get_logger("job_discovery")


class JobDiscoveryService:
    """Orchestrator for discovering raw job search results across multiple platform adapters."""
    
    def __init__(
        self,
        search_service: Optional[TavilySearchService] = None,
        registry: Optional[PlatformRegistry] = None
    ):
        self.settings = get_settings()
        self.search_service = search_service or TavilySearchService()
        self.registry = registry or PlatformRegistry(search_service=self.search_service)

    def discover_jobs(
        self,
        queries: List[SearchQuery],
        limit_per_query: int = 10
    ) -> DiscoveryResult:
        """
        Execute a set of search queries across platform adapters and return aggregated DiscoveryResult.
        
        Args:
            queries: List of SearchQuery objects.
            limit_per_query: Maximum raw results to fetch per query.
            
        Returns:
            DiscoveryResult containing normalized results, platform counts, and error logs.
        """
        if not queries:
            logger.warning("No search queries provided to JobDiscoveryService.")
            return DiscoveryResult()

        if getattr(self.settings, "DEMO_MODE", False) is True:
            logger.info("DEMO_MODE is active: Returning deterministic demo discovery results.")
            from app.services.demo_service import DemoService
            return DemoService.get_demo_discovery_result()


        # Check Tavily configuration first
        if not self.settings.is_tavily_configured():
            err_msg = "Please configure TAVILY_API_KEY to search real jobs."
            logger.error(err_msg)
            return DiscoveryResult(
                total_results=0,
                successful_queries=0,
                failed_queries=len(queries),
                platform_counts={},
                results=[],
                errors=[{
                    "error_type": "ConfigurationError",
                    "message": err_msg,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }]
            )

        collected_results: List[RawSearchResult] = []
        seen_urls: Set[str] = set()
        platform_counts: Dict[str, int] = {}
        successful_queries = 0
        failed_queries = 0
        errors: List[Dict[str, Any]] = []

        logger.info(f"Starting multi-platform discovery for {len(queries)} queries...")

        for query in queries:
            try:
                platform_name = query.platform.strip()
                adapter = self.registry.get_adapter(platform_name)
                
                if adapter and adapter.supports_query(query):
                    query_results = adapter.search(query, limit=limit_per_query)
                else:
                    # Fallback to general Tavily search
                    query_results = self.search_service.execute_search(
                        query_string=query.query_string,
                        max_results=limit_per_query,
                        target_platform=platform_name if platform_name not in ["General", "All"] else "Other"
                    )

                for item in query_results:
                    if item.url.lower() not in seen_urls:
                        seen_urls.add(item.url.lower())
                        collected_results.append(item)
                        platform_counts[item.platform] = platform_counts.get(item.platform, 0) + 1

                successful_queries += 1

            except Exception as e:
                failed_queries += 1
                error_record = {
                    "query": query.query_string,
                    "platform": query.platform,
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                logger.error(f"Platform search failed for query '{query.query_string}' on platform '{query.platform}': {e}")
                errors.append(error_record)

        result = DiscoveryResult(
            total_results=len(collected_results),
            successful_queries=successful_queries,
            failed_queries=failed_queries,
            platform_counts=platform_counts,
            results=collected_results,
            errors=errors
        )
        
        logger.info(
            f"Multi-platform discovery completed: {result.total_results} unique results discovered "
            f"({successful_queries} succeeded, {failed_queries} failed)"
        )
        return result
