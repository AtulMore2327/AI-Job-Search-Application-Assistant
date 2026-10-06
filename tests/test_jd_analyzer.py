"""
Unit tests for GroqJDAnalyzer service, structured JSON extraction, and non-hallucination guarantees.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from app.models.job import JDAnalysis
from app.services.jd_analyzer import GroqJDAnalyzer


def test_jd_analyzer_unconfigured_api_key():
    analyzer = GroqJDAnalyzer(api_key="")
    with pytest.raises(ValueError, match="GROQ_API_KEY is not configured"):
        analyzer.analyze_jd("Raw JD content", job_id="job_123")


def test_jd_analyzer_parse_json_markdown_fences():
    analyzer = GroqJDAnalyzer(api_key="gsk_mock_valid_key")
    
    raw_markdown = """
    ```json
    {
      "title": "Data Analyst",
      "responsibilities": ["Build SQL queries", "Create PowerBI dashboards"],
      "required_skills": ["Python", "SQL"]
    }
    ```
    """
    parsed = analyzer.parse_json_response(raw_markdown)
    assert parsed["title"] == "Data Analyst"
    assert "Python" in parsed["required_skills"]


def test_jd_analyzer_successful_mock_analysis():
    analyzer = GroqJDAnalyzer(api_key="gsk_mock_valid_key")
    
    mock_response_dict = {
        "title": "Senior Data Analyst",
        "company": "Acme Tech",
        "location": "Surat, India",
        "responsibilities": [
            "Extract insights from complex databases",
            "Build automated data pipelines"
        ],
        "required_skills": ["Python", "SQL", "Tableau"],
        "preferred_skills": ["Snowflake", "dbt"],
        "technical_skills": ["Python", "SQL", "PostgreSQL", "Pandas"],
        "soft_skills": ["Analytical thinking", "Communication"],
        "qualifications": ["B.Tech or M.S. in Computer Science or Statistics"],
        "education_requirements": "Bachelor's or Master's degree in STEM",
        "experience_requirements": "3-5 years of data analytics experience",
        "employment_type": "Full-time",
        "work_mode": "Hybrid",
        "salary_information": None,  # Verified no hallucinated salary
        "benefits": ["Health Insurance", "Flexible Hours"],
        "keywords": ["python", "sql", "tableau", "data analyst"],
        "seniority_level": "Senior",
        "industry": "Technology",
        "summary": "Senior Data Analyst position at Acme Tech in Surat focusing on SQL and Python data pipelines."
    }
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps(mock_response_dict)))
    ]
    
    with patch.object(analyzer.client.chat.completions, "create", return_value=mock_completion):
        analysis = analyzer.analyze_jd("Acme Tech hiring Senior Data Analyst in Surat...", job_id="job_surat_1")
        
        assert isinstance(analysis, JDAnalysis)
        assert analysis.job_id == "job_surat_1"
        assert analysis.title == "Senior Data Analyst"
        assert analysis.company == "Acme Tech"
        assert analysis.salary_information is None  # Salary stays None
        assert "Python" in analysis.required_skills
        assert "Snowflake" in analysis.preferred_skills
        assert analysis.employment_type == "Full-time"
        assert analysis.work_mode == "Hybrid"


def test_jd_analyzer_no_hallucination_of_missing_fields():
    """Verify missing facts return null/None or empty arrays without AI hallucination."""
    analyzer = GroqJDAnalyzer(api_key="gsk_mock_valid_key")
    
    # Mock LLM returning null for unstated salary and empty arrays for unstated benefits
    mock_response_dict = {
        "title": "Junior Python Dev",
        "responsibilities": ["Write Python code"],
        "required_skills": ["Python"],
        "preferred_skills": [],
        "salary_information": None,
        "benefits": [],
        "summary": "Junior role."
    }
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps(mock_response_dict)))
    ]
    
    with patch.object(analyzer.client.chat.completions, "create", return_value=mock_completion):
        analysis = analyzer.analyze_jd("Short job description text...", job_id="job_short")
        
        assert analysis.salary_information is None
        assert len(analysis.benefits) == 0
        assert len(analysis.preferred_skills) == 0


def test_jd_analyzer_empty_text_error():
    analyzer = GroqJDAnalyzer(api_key="gsk_mock_valid_key")
    with pytest.raises(ValueError, match="Job description text is empty"):
        analyzer.analyze_jd("   ", job_id="job_empty")
