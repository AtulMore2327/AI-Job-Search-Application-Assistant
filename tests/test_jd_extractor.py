"""
Unit tests for FullJDExtractor service, text cleaning, Schema.org parsing,
container selectors, text truncation limits, and HTTP failure isolation.
"""

import pytest
from unittest.mock import MagicMock, patch
import httpx

from app.models.job import Job, JDExtractResult
from app.services.jd_extractor import FullJDExtractor, clean_jd_text


def test_clean_jd_text_and_truncation():
    raw_text = "  Job Title  \x00\xa0\n\n\nResponsibilities:\n- Python & SQL  \nAccept all cookies to continue..."
    cleaned, truncated = clean_jd_text(raw_text, max_chars=1000)
    
    assert "Job Title" in cleaned
    assert "Accept all cookies" not in cleaned
    assert "\x00" not in cleaned
    assert truncated is False

    # Test size limit truncation
    long_text = "Word " * 5000  # ~25,000 chars
    cleaned_long, is_trunc = clean_jd_text(long_text, max_chars=100)
    assert is_trunc is True
    assert len(cleaned_long) <= 180
    assert "[Text truncated due to maximum size limits...]" in cleaned_long


def test_extract_jd_from_html_schema_org():
    extractor = FullJDExtractor()
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@type": "JobPosting",
          "title": "Data Analyst",
          "description": "<p>We are seeking a <b>Data Analyst</b> skilled in SQL and Tableau.</p>"
        }
        </script>
      </head>
      <body><div>Nav menu</div></body>
    </html>
    """
    
    res = extractor.extract_jd_from_html(html, "https://example.com/job/101", job_id="job_101")
    assert res.job_id == "job_101"
    assert res.accessible is True
    assert "Data Analyst" in res.raw_jd_text
    assert "SQL and Tableau" in res.raw_jd_text
    assert res.error is None


def test_extract_jd_from_html_semantic_containers():
    extractor = FullJDExtractor()
    html = """
    <html>
      <body>
        <nav>Nav Bar</nav>
        <div class="job-description">
          <h2>Role Overview</h2>
          <p>Develop RESTful APIs using Python and FastAPI in Surat.</p>
        </div>
        <footer>Footer Link</footer>
      </body>
    </html>
    """
    
    res = extractor.extract_jd_from_html(html, "https://example.com/job/202")
    assert "Develop RESTful APIs using Python and FastAPI" in res.raw_jd_text
    assert "Nav Bar" not in res.raw_jd_text
    assert "Footer Link" not in res.raw_jd_text


def test_extract_jd_from_url_http_404_dead_page():
    extractor = FullJDExtractor()
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    
    res = extractor.extract_jd_from_url("https://example.com/dead-job", job_id="job_dead", mock_client=mock_client)
    
    assert res.job_id == "job_dead"
    assert res.accessible is False
    assert res.raw_jd_text == ""
    assert "HTTP Error 404" in res.error


def test_extract_jd_from_url_timeout_exception():
    extractor = FullJDExtractor()
    
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("Read timeout")
    
    res = extractor.extract_jd_from_url("https://example.com/slow-job", job_id="job_slow", mock_client=mock_client)
    
    assert res.accessible is False
    assert res.raw_jd_text == ""
    assert "TimeoutException" in res.error or "Read timeout" in res.error


def test_extract_jd_batch_failure_isolation():
    extractor = FullJDExtractor()
    
    mock_resp_ok = MagicMock()
    mock_resp_ok.status_code = 200
    mock_resp_ok.text = "<html><body><div class='job-description'>Valid JD text for job 1</div></body></html>"
    
    mock_resp_fail = MagicMock()
    mock_resp_fail.status_code = 500
    
    def side_effect(url):
        if "fail" in url:
            return mock_resp_fail
        return mock_resp_ok
        
    mock_client = MagicMock()
    mock_client.get.side_effect = side_effect
    
    urls = ["https://example.com/job1", "https://example.com/fail-job2", "https://example.com/job3"]
    batch_res = extractor.extract_jd_batch(urls, mock_client=mock_client)
    
    assert len(batch_res) == 3
    assert batch_res[0].accessible is True
    assert "Valid JD text for job 1" in batch_res[0].raw_jd_text
    assert batch_res[1].accessible is False
    assert "HTTP Error 500" in batch_res[1].error
    assert batch_res[2].accessible is True
