"""
Unit tests for API endpoints: /jobs/filter, /jobs/match, /jobs/skill-gap, and /jobs/match/batch.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_filter_job_endpoint():
    payload = {
        "preferences": {
            "target_role": "Data Analyst",
            "location": "Surat",
            "work_mode": "Hybrid"
        },
        "job": {
            "job_id": "job_flt_1",
            "title": "Data Analyst",
            "company": "Tech Corp",
            "location": "Surat",
            "work_mode": "Hybrid",
            "canonical_url": "https://example.com/job/flt1"
        }
    }
    response = client.post("/jobs/filter", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "job_flt_1"
    assert data["passed"] is True
    assert len(data["checks"]) > 0


def test_match_job_endpoint():
    payload = {
        "candidate": {
            "name": "Jordan Lee",
            "skills": ["Python", "SQL", "Power BI"]
        },
        "job": {
            "job_id": "job_mtc_1",
            "title": "Data Analyst",
            "company": "Tech Corp",
            "canonical_url": "https://example.com/job/mtc1"
        },
        "jd_analysis": {
            "job_id": "job_mtc_1",
            "required_skills": ["Python", "SQL"],
            "preferred_skills": ["Power BI"]
        }
    }
    response = client.post("/jobs/match", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "job_mtc_1"
    assert data["match_score"] > 70.0
    assert "Python" in data["matched_required_skills"]
    assert "score_breakdown" in data
    assert "skill_gap" in data


def test_skill_gap_endpoint():
    payload = {
        "candidate": {
            "name": "Jordan Lee",
            "skills": ["Python", "SQL"]
        },
        "jd_analysis": {
            "job_id": "job_gap_1",
            "required_skills": ["Python", "SQL", "Tableau"],
            "preferred_skills": ["AWS"]
        }
    }
    response = client.post("/jobs/skill-gap", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Tableau" in data["critical_gaps"]
    assert "AWS" in data["secondary_gaps"]
    assert len(data["learning_suggestions"]) > 0


def test_batch_match_jobs_endpoint():
    payload = {
        "candidate": {
            "name": "Jordan Lee",
            "skills": ["Python", "SQL"]
        },
        "jobs": [
            {
                "job": {
                    "job_id": "batch_job_1",
                    "title": "Data Analyst",
                    "company": "Corp A",
                    "canonical_url": "https://example.com/job/b1"
                },
                "jd_analysis": {
                    "job_id": "batch_job_1",
                    "required_skills": ["Python", "SQL"]
                }
            },
            {
                "job": {
                    "job_id": "batch_job_2",
                    "title": "Backend Dev",
                    "company": "Corp B",
                    "canonical_url": "https://example.com/job/b2"
                },
                "jd_analysis": {
                    "job_id": "batch_job_2",
                    "required_skills": ["Java", "Spring"]
                }
            }
        ]
    }
    response = client.post("/jobs/match/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["job_id"] == "batch_job_1"
    assert data[1]["job_id"] == "batch_job_2"
