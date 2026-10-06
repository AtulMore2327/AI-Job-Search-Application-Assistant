"""
Unit tests for JobDiscoveryService orchestrator and platform failure isolation.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.config import Settings
from app.models.preferences import SearchQuery
from app.models.job import RawSearchResult, DiscoveryResult
from app.services.job_discovery import JobDiscoveryService
from app.platforms.tavily_search import TavilySearchService


def test_discovery_service_unconfigured_key():
    mock_settings = Settings(TAVILY_API_KEY="your_tavily_api_key_here")
    with patch("app.services.job_discovery.get_settings", return_value=mock_settings):
        service = JobDiscoveryService()
        queries = [SearchQuery(query_string="Data Analyst", platform="General", description="Test query")]
        res = service.discover_jobs(queries)
        
        assert res.total_results == 0
        assert res.failed_queries == 1
        assert len(res.errors) == 1
        assert "ConfigurationError" in res.errors[0]["error_type"]


def test_multi_query_discovery():
    mock_settings = Settings(TAVILY_API_KEY="tvly_mock_valid_key")
    
    mock_res_linkedin = [
        RawSearchResult(
            title="Data Analyst - LinkedIn",
            url="https://www.linkedin.com/jobs/view/1001",
            platform="LinkedIn",
            snippet="LinkedIn job post",
            query="LinkedIn query"
        )
    ]
    mock_res_naukri = [
        RawSearchResult(
            title="Data Analyst - Naukri",
            url="https://www.naukri.com/job/1002",
            platform="Naukri",
            snippet="Naukri job post",
            query="Naukri query"
        )
    ]

    with patch("app.services.job_discovery.get_settings", return_value=mock_settings), \
         patch("app.platforms.tavily_search.get_settings", return_value=mock_settings):
         
        service = JobDiscoveryService()
        
        queries = [
            SearchQuery(query_string='site:linkedin.com "Data Analyst"', platform="LinkedIn", description="LinkedIn search"),
            SearchQuery(query_string='site:naukri.com "Data Analyst"', platform="Naukri", description="Naukri search")
        ]
        
        with patch.object(service.registry.get_adapter("LinkedIn"), "search", return_value=mock_res_linkedin), \
             patch.object(service.registry.get_adapter("Naukri"), "search", return_value=mock_res_naukri):

            discovery_res = service.discover_jobs(queries)
            
            assert isinstance(discovery_res, DiscoveryResult)
            assert discovery_res.total_results == 2
            assert discovery_res.successful_queries == 2
            assert discovery_res.failed_queries == 0
            assert discovery_res.platform_counts.get("LinkedIn") == 1
            assert discovery_res.platform_counts.get("Naukri") == 1


def test_platform_failure_isolation():
    """Verify that if one platform search fails, other platforms continue executing."""
    mock_settings = Settings(TAVILY_API_KEY="tvly_mock_valid_key")
    
    mock_res_naukri = [
        RawSearchResult(
            title="Data Analyst - Naukri",
            url="https://www.naukri.com/job/1002",
            platform="Naukri",
            snippet="Naukri job post",
            query="Naukri query"
        )
    ]

    with patch("app.services.job_discovery.get_settings", return_value=mock_settings), \
         patch("app.platforms.tavily_search.get_settings", return_value=mock_settings):

        service = JobDiscoveryService()
        
        queries = [
            SearchQuery(query_string='site:linkedin.com "Data Analyst"', platform="LinkedIn", description="Failing LinkedIn search"),
            SearchQuery(query_string='site:naukri.com "Data Analyst"', platform="Naukri", description="Successful Naukri search")
        ]
        
        with patch.object(service.registry.get_adapter("LinkedIn"), "search", side_effect=RuntimeError("LinkedIn rate limit exceeded")), \
             patch.object(service.registry.get_adapter("Naukri"), "search", return_value=mock_res_naukri):

            discovery_res = service.discover_jobs(queries)
            
            assert discovery_res.total_results == 1
            assert discovery_res.successful_queries == 1
            assert discovery_res.failed_queries == 1
            assert len(discovery_res.errors) == 1
            assert discovery_res.errors[0]["platform"] == "LinkedIn"
            assert "LinkedIn rate limit exceeded" in discovery_res.errors[0]["message"]
