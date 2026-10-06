"""
Unit tests for URL validation, platform pattern classification, canonical normalization,
Schema.org JobPosting detection, and job link discovery.
"""

import pytest
from unittest.mock import MagicMock, patch
import httpx

from app.models.job import RawSearchResult, URLClassificationResult
from app.services.url_validator import normalize_canonical_url, URLClassifierService


def test_canonical_url_normalization():
    # Stripping tracking parameters
    url = "https://www.linkedin.com/jobs/view/123456/?utm_source=google&utm_medium=cpc&ref=xyz"
    canonical = normalize_canonical_url(url)
    assert canonical == "https://www.linkedin.com/jobs/view/123456"

    # Preserving essential job ID query params for Indeed
    indeed_url = "https://www.indeed.com/viewjob?jk=abcdef123456&utm_campaign=test"
    indeed_canonical = normalize_canonical_url(indeed_url)
    assert indeed_canonical == "https://www.indeed.com/viewjob?jk=abcdef123456"


def test_url_classification_patterns():
    service = URLClassifierService()

    # LinkedIn Individual vs Search vs Company
    c1, conf1, _ = service.classify_url_pattern("https://www.linkedin.com/jobs/view/12345", "LinkedIn")
    assert c1 == "INDIVIDUAL_JOB" and conf1 >= 0.85

    c2, conf2, _ = service.classify_url_pattern("https://www.linkedin.com/jobs/search?keywords=data", "LinkedIn")
    assert c2 == "SEARCH_PAGE" and conf2 >= 0.80

    c3, conf3, _ = service.classify_url_pattern("https://www.linkedin.com/company/google/", "LinkedIn")
    assert c3 == "COMPANY_PAGE" and conf3 >= 0.80

    # Naukri Individual vs Search
    c4, conf4, _ = service.classify_url_pattern("https://www.naukri.com/job-listings-data-analyst-12345", "Naukri")
    assert c4 == "INDIVIDUAL_JOB" and conf4 >= 0.85

    c5, conf5, _ = service.classify_url_pattern("https://www.naukri.com/data-analyst-jobs-in-surat", "Naukri")
    assert c5 == "SEARCH_PAGE" and conf5 >= 0.80

    # Indeed Individual vs Search
    c6, conf6, _ = service.classify_url_pattern("https://www.indeed.com/viewjob?jk=987654", "Indeed")
    assert c6 == "INDIVIDUAL_JOB" and conf6 >= 0.85

    # Company Careers ATS (Greenhouse / Lever)
    c7, conf7, _ = service.classify_url_pattern("https://boards.greenhouse.io/acme/jobs/99999", "CompanyCareers")
    assert c7 == "INDIVIDUAL_JOB" and conf7 >= 0.85


def test_invalid_url_classification():
    service = URLClassifierService()
    c, conf, _ = service.classify_url_pattern("not-a-valid-url", "Unknown")
    assert c == "INVALID"
    assert conf == 0.0


def test_http_validation_valid_individual_job():
    service = URLClassifierService()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://www.naukri.com/job-listings-data-analyst-12345"
    mock_response.text = """
    <html>
      <head>
        <title>Data Analyst - Acme Corp - Naukri</title>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "JobPosting",
          "title": "Data Analyst"
        }
        </script>
      </head>
      <body><h1>Data Analyst Position</h1></body>
    </html>
    """
    
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    
    res = service.validate_and_classify(
        item="https://www.naukri.com/job-listings-data-analyst-12345",
        fetch_html=True,
        mock_client=mock_client
    )
    
    assert res.classification == "INDIVIDUAL_JOB"
    assert res.has_job_posting_schema is True
    assert res.confidence >= 0.90
    assert "Schema.org JobPosting detected" in res.reason
    assert res.accessible is True
    assert res.http_status == 200


def test_http_validation_listing_page_discovers_links():
    service = URLClassifierService()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://www.naukri.com/data-analyst-jobs-in-surat"
    mock_response.text = """
    <html>
      <head><title>50 Data Analyst Jobs in Surat</title></head>
      <body>
        <a href="/job-listings-data-analyst-surat-1001">Job 1</a>
        <a href="/job-listings-python-developer-surat-1002">Job 2</a>
        <a href="/company/about-us">About Us</a>
      </body>
    </html>
    """
    
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    
    res = service.validate_and_classify(
        item="https://www.naukri.com/data-analyst-jobs-in-surat",
        fetch_html=True,
        mock_client=mock_client
    )
    
    assert res.classification == "LISTING_PAGE"
    assert res.accessible is True
    assert len(res.discovered_job_urls) == 2
    assert "https://www.naukri.com/job-listings-data-analyst-surat-1001" in res.discovered_job_urls


def test_http_validation_inaccessible_dead_url():
    service = URLClassifierService()
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.url = "https://www.example.com/job/404"
    
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    
    res = service.validate_and_classify(
        item="https://www.example.com/job/404",
        fetch_html=True,
        mock_client=mock_client
    )
    
    assert res.accessible is False
    assert res.http_status == 404
    assert res.error == "HTTP Error 404"
    assert res.classification == "INVALID"


def test_http_validation_timeout_error():
    service = URLClassifierService()
    
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")
    
    res = service.validate_and_classify(
        item="https://www.example.com/slow-job",
        fetch_html=True,
        mock_client=mock_client
    )
    
    assert res.accessible is False
    assert res.http_status is None
    assert "TimeoutException" in res.reason or "Connection timed out" in str(res.error)


def test_http_validation_redirect_resolution():
    service = URLClassifierService()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://www.linkedin.com/jobs/view/999888777"
    mock_response.text = "<html><head><title>LinkedIn Job View</title></head></html>"
    
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    
    original = "http://short.url/job123"
    res = service.validate_and_classify(
        item=original,
        fetch_html=True,
        mock_client=mock_client
    )
    
    assert res.original_url == original
    assert res.final_url == "https://www.linkedin.com/jobs/view/999888777"
    assert res.classification == "INDIVIDUAL_JOB"


def test_batch_classification_with_single_failure_isolation():
    service = URLClassifierService()
    
    items = [
        "https://www.linkedin.com/jobs/view/11111",
        "invalid-url-item",
        "https://www.naukri.com/job-listings-22222"
    ]
    
    results = service.validate_and_classify_batch(items, fetch_html=False)
    
    assert len(results) == 3
    assert results[0].classification == "INDIVIDUAL_JOB"
    assert results[1].classification == "INVALID"
    assert results[2].classification == "INDIVIDUAL_JOB"


def test_verified_individual_job_url_rules():
    """
    Regression test verifying:
    - Valid individual job URL passes verification
    - Listing page URL is rejected
    - Search page URL is rejected
    - Localhost/API URL is rejected
    - Valid canonical_url is preferred over source URL
    - Fallback to valid source URL occurs if canonical_url is search/listing
    - Missing/invalid URLs return None
    """
    # 1. Valid individual job URL opens correctly
    valid_job_url = "https://www.linkedin.com/jobs/view/38291023"
    assert URLClassifierService.is_valid_individual_job_url(valid_job_url) is True

    # 2. Listing URL is rejected
    listing_url = "https://www.naukri.com/data-analyst-jobs-in-surat"
    assert URLClassifierService.is_valid_individual_job_url(listing_url) is False

    # 3. Search URL is rejected
    search_url = "https://www.linkedin.com/jobs/search?keywords=python"
    assert URLClassifierService.is_valid_individual_job_url(search_url) is False

    # 4. Localhost / API URL is rejected
    localhost_url = "http://127.0.0.1:8000/api/jobs"
    assert URLClassifierService.is_valid_individual_job_url(localhost_url) is False

    # 5. Preferred canonical_url over non-canonical source URL
    canonical = "https://www.linkedin.com/jobs/view/38291023"
    sources = ["https://www.linkedin.com/jobs/search?keywords=python", "https://short.url/xyz"]
    verified = URLClassifierService.get_verified_job_url(canonical, sources)
    assert verified == canonical

    # 6. Fallback to valid source URL if canonical_url is search page
    search_canonical = "https://www.linkedin.com/jobs/search?keywords=python"
    valid_source = ["https://www.linkedin.com/jobs/view/38291023"]
    verified_fallback = URLClassifierService.get_verified_job_url(search_canonical, valid_source)
    assert verified_fallback == "https://www.linkedin.com/jobs/view/38291023"

    # 7. Missing / invalid URL returns None
    assert URLClassifierService.get_verified_job_url("", ["invalid-url"]) is None
    assert URLClassifierService.get_verified_job_url("http://127.0.0.1:8000", []) is None

