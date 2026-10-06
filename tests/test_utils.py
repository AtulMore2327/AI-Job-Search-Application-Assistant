"""
Tests for text, URL, and retry utilities.
"""

import pytest
from app.utils.text import clean_text, extract_keywords
from app.utils.urls import normalize_url
from app.utils.retry import retry_with_backoff

def test_clean_text():
    assert clean_text("  hello   world \n\t ") == "hello world"
    assert clean_text("") == ""

def test_extract_keywords():
    keywords = extract_keywords("Python Developer with FastAPI & SQL experience!")
    assert "python" in keywords
    assert "developer" in keywords
    assert "fastapi" in keywords
    assert "sql" in keywords

def test_normalize_url():
    url = "HTTPS://WWW.Example.com/Jobs/123/?utm_source=google&ref=123"
    normalized = normalize_url(url)
    assert normalized == "https://www.example.com/Jobs/123"

def test_retry_with_backoff_success():
    attempts = 0

    @retry_with_backoff(retries=2, backoff_in_seconds=0.01)
    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("Temporary failure")
        return "success"

    result = flaky_func()
    assert result == "success"
    assert attempts == 2

def test_retry_with_backoff_failure():
    @retry_with_backoff(retries=2, backoff_in_seconds=0.01, exceptions=(ValueError,))
    def always_fails():
        raise ValueError("Permanent failure")

    with pytest.raises(ValueError, match="Permanent failure"):
        always_fails()
