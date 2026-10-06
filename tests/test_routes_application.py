"""
Unit tests for API routes in /applications (/generate, /cover-letter, /email, /linkedin).
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_generate_application_package_endpoint_success():
    payload = {
        "candidate": {
            "name": "Jordan Lee",
            "email": "jordan.lee@example.com",
            "skills": ["Python", "SQL", "Tableau"]
        },
        "job": {
            "job_id": "job_app_test_10",
            "title": "Data Analyst",
            "company": "Analytics Corp",
            "canonical_url": "https://example.com/job/app10"
        }
    }
    response = client.post("/applications/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "job_app_test_10"
    assert data["candidate_name"] == "Jordan Lee"
    assert data["company"] == "Analytics Corp"
    assert "cover_letter" in data
    assert "email_draft" in data
    assert "linkedin_connection" in data
    assert "linkedin_recruiter" in data
    assert "linkedin_followup" in data


def test_generate_cover_letter_endpoint():
    payload = {
        "candidate": {
            "name": "Jordan Lee",
            "skills": ["Python", "SQL"]
        },
        "job": {
            "job_id": "job_cl_test",
            "title": "Junior Data Analyst",
            "company": "Data Ltd",
            "canonical_url": "https://example.com/job/cltest"
        }
    }
    response = client.post("/applications/cover-letter", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "job_cl_test"
    assert "Jordan Lee" in data["full_text"]
    assert "Data Ltd" in data["full_text"]


def test_generate_email_endpoint():
    payload = {
        "candidate": {
            "name": "Jordan Lee",
            "email": "jordan@example.com",
            "skills": ["Python"]
        },
        "job": {
            "job_id": "job_email_test",
            "title": "Python Developer",
            "company": "Py Corp",
            "canonical_url": "https://example.com/job/emailtest"
        }
    }
    response = client.post("/applications/email", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "job_email_test"
    assert "Application for Python Developer - Jordan Lee" in data["subject"]


def test_generate_linkedin_endpoint():
    payload = {
        "candidate": {
            "name": "Jordan Lee",
            "skills": ["Python"]
        },
        "job": {
            "job_id": "job_li_test",
            "title": "Python Developer",
            "company": "Py Corp",
            "canonical_url": "https://example.com/job/litest"
        }
    }
    response = client.post("/applications/linkedin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "connection" in data
    assert "recruiter" in data
    assert "followup" in data
    assert data["connection"]["purpose"] == "connection"
