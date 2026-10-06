"""
Unit tests for Tavily search provider, platform detection, and retry mechanism.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.config import Settings
from app.platforms.tavily_search import TavilySearchService
from app.utils.urls import detect_platform_from_url


def test_platform_detection_from_url():
    assert detect_platform_from_url("https://www.linkedin.com/jobs/view/123456") == "LinkedIn"
    assert detect_platform_from_url("https://www.naukri.com/job-listings-data-analyst") == "Naukri"
    assert detect_platform_from_url("https://in.indeed.com/viewjob?jk=abcdef") == "Indeed"
    assert detect_platform_from_url("https://internshala.com/internship/detail/123") == "Internshala"
    assert detect_platform_from_url("https://www.foundit.in/job/data-analyst") == "Foundit"
    assert detect_platform_from_url("https://wellfound.com/jobs/999-developer") == "Wellfound"
    assert detect_platform_from_url("https://www.hirist.com/j/data-analyst-123.html") == "Hirist"
    assert detect_platform_from_url("https://www.glassdoor.com/Job/surat-data-analyst-jobs") == "Glassdoor"
    assert detect_platform_from_url("https://www.shine.com/jobs/data-analyst/123") == "Shine"
    assert detect_platform_from_url("https://www.timesjobs.com/job-detail/123") == "TimesJobs"
    assert detect_platform_from_url("https://cutshort.io/job/python-dev") == "Cutshort"
    assert detect_platform_from_url("https://apna.co/job/data-analyst-in-surat") == "Apna"
    assert detect_platform_from_url("https://www.workindia.in/job/12345") == "WorkIndia"
    assert detect_platform_from_url("https://boards.greenhouse.io/company/jobs/123") == "CompanyCareers"
    assert detect_platform_from_url("https://jobs.lever.co/company/abc-123") == "CompanyCareers"
    assert detect_platform_from_url("https://unknowncompany.com/page") == "Other"


def test_missing_tavily_api_key():
    service = TavilySearchService(api_key="")
    with pytest.raises(ValueError, match="TAVILY_API_KEY is not configured"):
        service.execute_search("Data Analyst Surat")


def test_tavily_successful_search():
    mock_tavily_response = {
        "results": [
            {
                "title": "Data Analyst Job in Surat",
                "url": "https://www.naukri.com/job-listings-data-analyst-surat-123?utm_source=google",
                "content": "Looking for a Data Analyst proficient in Python and SQL in Surat.",
                "score": 0.95
            },
            {
                "title": "Junior BI Developer - Surat",
                "url": "https://www.linkedin.com/jobs/view/987654",
                "content": "ABC Tech is hiring a Junior BI Analyst in Surat.",
                "score": 0.88
            }
        ]
    }
    
    with patch("tavily.TavilyClient") as mock_client_class:
        mock_instance = MagicMock()
        mock_instance.search.return_value = mock_tavily_response
        mock_client_class.return_value = mock_instance
        
        service = TavilySearchService(api_key="tvly_mock_valid_key")
        service.client = mock_instance
        
        results = service.execute_search("Data Analyst Surat", max_results=5)
        
        assert len(results) == 2
        
        res1 = results[0]
        assert res1.title == "Data Analyst Job in Surat"
        assert res1.url == "https://www.naukri.com/job-listings-data-analyst-surat-123"
        assert res1.platform == "Naukri"
        assert res1.score == 0.95
        
        res2 = results[1]
        assert res2.platform == "LinkedIn"
        assert res2.score == 0.88


def test_empty_search_results():
    with patch("tavily.TavilyClient") as mock_client_class:
        mock_instance = MagicMock()
        mock_instance.search.return_value = {"results": []}
        mock_client_class.return_value = mock_instance
        
        service = TavilySearchService(api_key="tvly_mock_valid_key")
        service.client = mock_instance
        
        results = service.execute_search("Unusual Nonexistent Job Search Query")
        assert len(results) == 0


def test_tavily_retry_behavior():
    attempts = 0
    
    def mock_flaky_search(**kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionError("Temporary API Timeout")
        return {"results": [{"title": "Retry Success", "url": "https://example.com/job", "content": "Flaky success"}]}
        
    with patch("tavily.TavilyClient") as mock_client_class:
        mock_instance = MagicMock()
        mock_instance.search.side_effect = mock_flaky_search
        mock_client_class.return_value = mock_instance
        
        service = TavilySearchService(api_key="tvly_mock_valid_key")
        service.client = mock_instance
        
        results = service.execute_search("Flaky query")
        
        assert attempts == 2
        assert len(results) == 1
        assert results[0].title == "Retry Success"


def test_tavily_api_failure_handling():
    with patch("tavily.TavilyClient") as mock_client_class:
        mock_instance = MagicMock()
        mock_instance.search.side_effect = RuntimeError("Fatal API Key Exception")
        mock_client_class.return_value = mock_instance
        
        service = TavilySearchService(api_key="tvly_mock_valid_key")
        service.client = mock_instance
        
        with pytest.raises(RuntimeError, match="Fatal API Key Exception"):
            service.execute_search("Failing Query")
