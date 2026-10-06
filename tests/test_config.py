"""
Tests for configuration system.
"""

import os
from pathlib import Path
from app.config import Settings, get_settings, reload_settings, BASE_DIR

def test_default_settings():
    settings = Settings()
    assert settings.APP_NAME == "10X AI Job Search & Application System"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.DEMO_MODE is False
    assert settings.LOG_LEVEL == "INFO"
    assert settings.HOST == "127.0.0.1"
    assert settings.PORT == 8000

def test_api_key_configuration_check():
    settings = Settings(GROQ_API_KEY="your_groq_api_key_here", TAVILY_API_KEY="")
    assert settings.is_groq_configured() is False
    assert settings.is_tavily_configured() is False

    settings_valid = Settings(GROQ_API_KEY="gsk_real_key_12345", TAVILY_API_KEY="tvly_real_key_67890")
    assert settings_valid.is_groq_configured() is True
    assert settings_valid.is_tavily_configured() is True

def test_directory_creation(tmp_path):
    custom_data = tmp_path / "custom_data"
    custom_exports = tmp_path / "custom_exports"
    custom_logs = tmp_path / "custom_data" / "logs"
    
    settings = Settings(
        DATA_DIR=custom_data,
        EXPORTS_DIR=custom_exports,
        LOGS_DIR=custom_logs
    )
    settings.ensure_directories()
    
    assert custom_data.exists()
    assert custom_exports.exists()
    assert custom_logs.exists()

def test_singleton_get_settings():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_config_status_endpoint():
    """Verify /config/status endpoint returns safe status labels without exposing key values."""
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    res = client.get("/config/status")
    assert res.status_code == 200
    data = res.json()

    assert "Tavily" in data
    assert "Groq" in data
    assert "Demo Mode" in data

    assert data["Tavily"] in ["configured", "missing"]
    assert data["Groq"] in ["configured", "missing"]
    assert isinstance(data["Demo Mode"], bool)

    # Ensure secret values are never exposed
    for val in data.values():
        val_str = str(val)
        assert "gsk_" not in val_str
        assert "tvly_" not in val_str


def test_groq_missing_clear_error_message(monkeypatch):
    """Verify missing GROQ_API_KEY in real mode raises 'Please configure GROQ_API_KEY for AI analysis.'"""
    from app.services.resume_analyzer import ResumeAnalyzer
    import pytest

    try:
        monkeypatch.setenv("DEMO_MODE", "false")
        monkeypatch.setenv("GROQ_API_KEY", "")
        reload_settings()

        analyzer = ResumeAnalyzer(api_key="")
        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze_resume("Valid resume text for testing")
        
        assert "Please configure GROQ_API_KEY for AI analysis." in str(exc_info.value)
    finally:
        monkeypatch.undo()
        reload_settings()


def test_tavily_missing_clear_error_message(monkeypatch):
    """Verify missing TAVILY_API_KEY in real mode outputs 'Please configure TAVILY_API_KEY to search real jobs.'"""
    from app.services.job_discovery import JobDiscoveryService
    from app.models.preferences import SearchQuery

    try:
        monkeypatch.setenv("DEMO_MODE", "false")
        monkeypatch.setenv("TAVILY_API_KEY", "")
        reload_settings()

        discovery = JobDiscoveryService()
        queries = [
            SearchQuery(query_string="Python Indore", platform="LinkedIn", query_type="Role", description="Desc")
        ]
        result = discovery.discover_jobs(queries)
        assert result.total_results == 0
        assert len(result.errors) > 0
        assert "Please configure TAVILY_API_KEY to search real jobs." in result.errors[0]["message"]
    finally:
        monkeypatch.undo()
        reload_settings()

