"""
Unit tests for resume PDF extraction and Groq-based resume analyzer service.
"""

import io
import pytest
from unittest.mock import MagicMock, patch

from app.models.candidate import CandidateProfile, EducationItem, ExperienceItem, ProjectItem
from app.services.resume_analyzer import extract_text_from_pdf, ResumeAnalyzer
from app.utils.text import clean_resume_text

# Helper function to generate valid PDF bytes for testing
def create_sample_pdf_bytes(text: str = "Jane Doe - Senior Data Analyst") -> bytes:
    stream_content = f"BT /F1 12 Tf 100 700 Td ({text}) Tj ET".encode('ascii')
    length = len(stream_content)
    obj1 = b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    obj2 = b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    obj3 = b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources <</Font <</F1 4 0 R>>>> /Contents 5 0 R>> endobj\n"
    obj4 = b"4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
    obj5 = b"5 0 obj <</Length " + str(length).encode('ascii') + b">> stream\n" + stream_content + b"\nendstream\nendobj\n"
    header = b"%PDF-1.4\n"
    offset1 = len(header)
    offset2 = offset1 + len(obj1)
    offset3 = offset2 + len(obj2)
    offset4 = offset3 + len(obj3)
    offset5 = offset4 + len(obj4)
    xref_offset = offset5 + len(obj5)
    xref = (
        b"xref\n0 6\n0000000000 65535 f \n"
        + f"{offset1:010d} 00000 n \n".encode('ascii')
        + f"{offset2:010d} 00000 n \n".encode('ascii')
        + f"{offset3:010d} 00000 n \n".encode('ascii')
        + f"{offset4:010d} 00000 n \n".encode('ascii')
        + f"{offset5:010d} 00000 n \n".encode('ascii')
    )
    trailer = b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n" + str(xref_offset).encode('ascii') + b"\n%%EOF\n"
    return header + obj1 + obj2 + obj3 + obj4 + obj5 + xref + trailer


def test_extract_text_from_pdf_success():
    pdf_bytes = create_sample_pdf_bytes("Jane Doe - Senior Data Analyst")
    text = extract_text_from_pdf(pdf_bytes)
    assert "Jane Doe" in text
    assert "Senior Data Analyst" in text


def test_extract_text_from_pdf_empty_bytes():
    with pytest.raises(ValueError, match="PDF content is empty"):
        extract_text_from_pdf(b"")


def test_extract_text_from_pdf_invalid_bytes():
    with pytest.raises(ValueError):
        extract_text_from_pdf(b"Not a valid PDF header")


def test_clean_resume_text_formatting():
    raw_text = "  John Doe  \x00\xa0\n\n\n\nSoftware Engineer \t\n\nPython & SQL  "
    cleaned = clean_resume_text(raw_text)
    assert "John Doe" in cleaned
    assert "Software Engineer" in cleaned
    assert "\x00" not in cleaned
    assert "\xa0" not in cleaned
    # Ensure excess consecutive empty lines are collapsed
    assert "\n\n\n" not in cleaned


def test_resume_analyzer_unconfigured():
    analyzer = ResumeAnalyzer(api_key="")
    with pytest.raises(ValueError, match="GROQ_API_KEY is not configured"):
        analyzer.analyze_resume("Sample resume text")


def test_resume_analyzer_parse_json_response():
    analyzer = ResumeAnalyzer(api_key="gsk_dummy_test_key")
    
    # 1. Clean JSON
    json_str = '{"name": "Alice Smith", "skills": ["Python", "SQL"]}'
    parsed = analyzer.parse_json_response(json_str)
    assert parsed["name"] == "Alice Smith"
    assert "Python" in parsed["skills"]

    # 2. Markdown fenced JSON
    fenced_str = "```json\n{\n  \"name\": \"Bob\",\n  \"skills\": [\"Java\"]\n}\n```"
    parsed_fenced = analyzer.parse_json_response(fenced_str)
    assert parsed_fenced["name"] == "Bob"
    assert "Java" in parsed_fenced["skills"]


def test_resume_analyzer_analyze_mocked():
    analyzer = ResumeAnalyzer(api_key="gsk_mock_valid_key")
    
    mock_llm_json = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+1-555-0199",
        "location": "San Francisco, CA",
        "summary": "Experienced Data Scientist with background in ML and Python.",
        "education": [
            {
                "degree": "M.S. in Data Science",
                "institution": "Stanford University",
                "year": "2022",
                "location": "Stanford, CA",
                "grade": "3.9 GPA"
            }
        ],
        "experience": [
            {
                "title": "Data Analyst",
                "company": "Acme Corp",
                "duration": "2022 - Present",
                "location": "Remote",
                "responsibilities": ["Built predictive ML models", "Automated SQL reporting"],
                "technologies": ["Python", "SQL", "Pandas", "Scikit-Learn"]
            }
        ],
        "projects": [
            {
                "title": "Sales Forecasting Model",
                "description": "Time-series forecasting for retail inventory",
                "role": "Lead Developer",
                "technologies": ["Python", "Prophet"],
                "url": "https://github.com/janedoe/sales-forecast"
            }
        ],
        "skills": ["Python", "SQL", "Machine Learning", "Data Analysis"],
        "tools": ["Git", "Docker", "Jupyter"],
        "certifications": ["AWS Certified Data Analytics"],
        "industries": ["E-commerce", "Technology"],
        "keywords": ["python", "sql", "machine learning", "data scientist"]
    }
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=str(mock_llm_json).replace("'", '"')))
    ]
    
    with patch.object(analyzer.client.chat.completions, "create", return_value=mock_completion):
        profile = analyzer.analyze_resume("Jane Doe\nData Scientist\nPython SQL Machine Learning")
        
        assert isinstance(profile, CandidateProfile)
        assert profile.name == "Jane Doe"
        assert profile.email == "jane.doe@example.com"
        assert len(profile.education) == 1
        assert profile.education[0].degree == "M.S. in Data Science"
        assert len(profile.experience) == 1
        assert profile.experience[0].company == "Acme Corp"
        assert "Python" in profile.skills
        assert "Git" in profile.tools
        assert profile.raw_text is not None
