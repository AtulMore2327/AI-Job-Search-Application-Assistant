import pytest
from app.utils.text import clean_text, normalize_title, normalize_company, extract_keywords
from app.utils.urls import clean_url, extract_domain

def test_clean_text():
    raw = "Hello   World!\r\n\r\nThis is\ta test\x00 text."
    cleaned = clean_text(raw)
    assert "Hello World!" in cleaned
    assert "\x00" not in cleaned

def test_normalize_title():
    assert normalize_title("Data Analyst (Junior) - Fulltime") == "data analyst junior fulltime"

def test_normalize_company():
    assert normalize_company("TechCorp Pvt Ltd") == "techcorp"
    assert normalize_company("Acme Solutions Inc.") == "acme"

def test_extract_keywords():
    kw = extract_keywords("Looking for Python, SQL, and Power BI skills")
    assert "python" in kw
    assert "sql" in kw

def test_clean_url_strips_tracking():
    url = "https://www.naukri.com/job-listings-123?utm_source=google&gclid=xyz&ref=search"
    cleaned = clean_url(url)
    assert "utm_source" not in cleaned
    assert "gclid" not in cleaned
    assert cleaned == "https://www.naukri.com/job-listings-123"

def test_extract_domain():
    assert extract_domain("https://www.glassdoor.com/job-listing/123") == "glassdoor.com"
