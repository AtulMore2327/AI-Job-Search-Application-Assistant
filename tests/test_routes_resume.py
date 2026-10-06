"""
Unit tests for resume API routes (/resume/upload and /resume/analyze).
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings
from tests.test_resume_analyzer import create_sample_pdf_bytes

client = TestClient(app)


def test_upload_resume_endpoint_success():
    pdf_bytes = create_sample_pdf_bytes("John Developer - Python & SQL Expert")
    files = {"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    
    response = client.post("/resume/upload", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "resume.pdf"
    assert "John Developer" in data["cleaned_text"]
    assert "python" in data["keywords"] or "developer" in data["keywords"]


def test_upload_resume_endpoint_invalid_extension():
    files = {"file": ("resume.txt", b"Plain text content", "text/plain")}
    response = client.post("/resume/upload", files=files)
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_analyze_resume_endpoint_with_text():
    mock_profile_dict = {
        "name": "Alex Smith",
        "email": "alex@example.com",
        "phone": "+1-555-0100",
        "location": "New York, NY",
        "summary": "Full Stack Software Engineer",
        "education": [
            {
                "degree": "B.S. Computer Science",
                "institution": "NYU",
                "year": "2021",
                "location": "New York",
                "grade": "3.8"
            }
        ],
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "duration": "2021-Present",
                "location": "New York",
                "responsibilities": ["Built REST APIs with FastAPI"],
                "technologies": ["Python", "FastAPI"]
            }
        ],
        "projects": [],
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "tools": ["Git", "Docker"],
        "certifications": [],
        "industries": ["Technology"],
        "keywords": ["python", "fastapi", "software engineer"]
    }

    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps(mock_profile_dict)))
    ]

    mock_settings = Settings(GROQ_API_KEY="gsk_mock_valid_key")

    with patch("app.services.resume_analyzer.get_settings", return_value=mock_settings), \
         patch("groq.Groq") as mock_groq_class:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_groq_class.return_value = mock_instance

        payload = {"resume_text": "Alex Smith\nSoftware Engineer\nPython FastAPI PostgreSQL"}
        response = client.post("/resume/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alex Smith"
        assert data["email"] == "alex@example.com"
        assert "Python" in data["skills"]


def test_analyze_resume_endpoint_with_pdf():
    pdf_bytes = create_sample_pdf_bytes("Alex Smith - Full Stack Developer")
    
    mock_profile_dict = {
        "name": "Alex Smith",
        "email": "alex@example.com",
        "skills": ["Python", "JavaScript"]
    }
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps(mock_profile_dict)))
    ]

    mock_settings = Settings(GROQ_API_KEY="gsk_mock_valid_key")

    with patch("app.services.resume_analyzer.get_settings", return_value=mock_settings), \
         patch("groq.Groq") as mock_groq_class:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_groq_class.return_value = mock_instance

        files = {"file": ("alex_resume.pdf", pdf_bytes, "application/pdf")}
        response = client.post("/resume/analyze", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alex Smith"
        assert "Python" in data["skills"]


def test_analyze_resume_endpoint_unconfigured_key():
    payload = {"resume_text": "Sample resume text"}
    mock_settings = Settings(GROQ_API_KEY="your_groq_api_key_here")
    
    with patch("app.services.resume_analyzer.get_settings", return_value=mock_settings):
        response = client.post("/resume/analyze", json=payload)
        assert response.status_code == 400
        assert "GROQ_API_KEY is not configured" in response.json()["detail"]
