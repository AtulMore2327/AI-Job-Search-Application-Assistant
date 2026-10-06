"""
Regression tests for Match Analysis, JD Analysis, Caching, and Skill Gap flow.
Covers all 15 scenarios specified in Section 12 of the requirement.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.job import JDAnalysis, Job
from app.models.candidate import CandidateProfile
from app.models.matching import MatchResult
from app.services.jd_analyzer import GroqJDAnalyzer, create_fallback_jd_analysis
from app.services.skill_gap import SkillGapService
from app.database.connection import get_db_connection
from app.database.repositories import JDCacheRepository, MatchCacheRepository


client = TestClient(app)


# 1. JDAnalysis receives valid dictionary
def test_jd_analysis_valid_dict():
    data = {
        "job_id": "job_101",
        "title": "Backend Engineer",
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["Docker"],
        "summary": "Great backend role"
    }
    analysis = JDAnalysis(**data)
    assert analysis.job_id == "job_101"
    assert analysis.title == "Backend Engineer"
    assert "Python" in analysis.required_skills


# 2. JDAnalysis never receives None
def test_jd_analysis_never_receives_none():
    fallback = create_fallback_jd_analysis("job_102", title="Python Developer")
    assert isinstance(fallback, JDAnalysis)
    assert fallback.job_id == "job_102"
    assert fallback.title == "Python Developer"
    assert isinstance(fallback.required_skills, list)


# 3. JD analyzer returns valid fallback
def test_jd_analyzer_returns_valid_fallback():
    fallback = create_fallback_jd_analysis("job_fallback_1", title="Data Analyst")
    assert isinstance(fallback, JDAnalysis)
    assert fallback.job_id == "job_fallback_1"
    assert fallback.required_skills == []


# 4. JD analyzer handles Groq failure
def test_jd_analyzer_handles_groq_failure():
    analyzer = GroqJDAnalyzer(api_key="gsk_dummy")
    with patch.object(analyzer.client.chat.completions, "create", side_effect=Exception("Groq API Timeout")):
        with pytest.raises((RuntimeError, Exception)):
            analyzer.analyze_jd("Python job requirements...", job_id="job_groq_fail")


# 5. JD analyzer handles invalid JSON
def test_jd_analyzer_handles_invalid_json():
    analyzer = GroqJDAnalyzer(api_key="gsk_dummy")
    mock_comp = MagicMock()
    mock_comp.choices = [MagicMock(message=MagicMock(content="Invalid JSON output response"))]
    with patch.object(analyzer.client.chat.completions, "create", return_value=mock_comp):
        with pytest.raises(ValueError):
            analyzer.analyze_jd("Some JD text...", job_id="job_json_fail")


# 6. JD cache contains analysis
def test_jd_cache_contains_analysis(tmp_path):
    repo = JDCacheRepository()
    analysis = create_fallback_jd_analysis("job_cached_1", title="DevOps Engineer")
    repo.save_jd_analysis(analysis, raw_jd_text="Full JD text")
    cached = repo.get_jd_analysis(job_id="job_cached_1")
    assert cached is not None
    assert cached.job_id == "job_cached_1"


# 7. JD cache contains NULL/invalid analysis
def test_jd_cache_contains_null_analysis():
    repo = JDCacheRepository()
    with get_db_connection() as db:
        db.execute(
            "INSERT OR REPLACE INTO jd_cache (job_id, raw_jd_text, jd_analysis_json, extracted_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            ("job_null_cache", "Raw text", "null")
        )
    cached = repo.get_jd_analysis(job_id="job_null_cache")
    assert cached is None  # Must gracefully return None, not crash




# 8. Skill gap works with valid JD analysis
def test_skill_gap_valid_jd():
    service = SkillGapService()
    candidate = CandidateProfile(name="Alex", skills=["Python", "FastAPI"])
    jd = JDAnalysis(job_id="j1", required_skills=["Python", "FastAPI", "Docker"], preferred_skills=["Kubernetes"])
    gap = service.analyze_gap(
        candidate=candidate,
        jd_analysis=jd,
        matched_required=["Python", "FastAPI"],
        missing_required=["Docker"],
        matched_preferred=[],
        missing_preferred=["Kubernetes"]
    )
    assert "Docker" in gap.critical_gaps
    assert "Kubernetes" in gap.secondary_gaps


# 9. Skill gap handles missing JD analysis (None)
def test_skill_gap_handles_missing_jd():
    service = SkillGapService()
    candidate = CandidateProfile(name="Alex", skills=["Python"])
    gap = service.analyze_gap(
        candidate=candidate,
        jd_analysis=None,
        matched_required=[],
        missing_required=[],
        matched_preferred=[],
        missing_preferred=[]
    )
    assert gap is not None
    assert len(gap.critical_gaps) == 0
    assert any("unavailable" in s.lower() for s in gap.learning_suggestions)


# 10. Skill gap handles empty skills
def test_skill_gap_empty_skills():
    service = SkillGapService()
    candidate = CandidateProfile(name="No Skills Alex", skills=[])
    jd = JDAnalysis(job_id="j_empty_skills", required_skills=[], preferred_skills=[])
    gap = service.analyze_gap(
        candidate=candidate,
        jd_analysis=jd,
        matched_required=[],
        missing_required=[],
        matched_preferred=[],
        missing_preferred=[]
    )
    assert len(gap.critical_gaps) == 0
    assert len(gap.secondary_gaps) == 0


# 11. /jobs/skill-gap does not produce 500 for missing analysis
def test_route_skill_gap_missing_analysis():
    payload = {
        "candidate": {
            "name": "Jane",
            "skills": ["Python"]
        },
        "job": {
            "id": "job_missing_jd",
            "job_id": "job_missing_jd",
            "title": "Software Engineer",
            "company": "Tech Corp",
            "location": "Remote",
            "canonical_url": "http://example.com/job_missing_jd"
        },
        "jd_analysis": None,
        "match_result": {
            "match_score": 75.0,
            "matched_required": ["Python"],
            "missing_required": [],
            "matched_preferred": [],
            "missing_preferred": [],
            "explanation": "Good match"
        }
    }
    response = client.post("/jobs/skill-gap", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "critical_gaps" in data
    assert "secondary_gaps" in data


# 12. Match -> skill gap complete flow
def test_match_to_skill_gap_flow():
    candidate_payload = {
        "name": "Alice",
        "skills": ["Python", "SQL"]
    }
    job_payload = {
        "id": "job_flow_1",
        "job_id": "job_flow_1",
        "title": "Data Engineer",
        "company": "DataCorp",
        "location": "Indore",
        "canonical_url": "http://datacorp.com/jobs/1"
    }
    jd_payload = {
        "job_id": "job_flow_1",
        "required_skills": ["Python", "SQL", "Spark"],
        "preferred_skills": ["AWS"]
    }
    
    # 1. Match
    match_resp = client.post("/jobs/match", json={
        "candidate": candidate_payload,
        "job": job_payload,
        "jd_analysis": jd_payload
    })
    assert match_resp.status_code == 200
    match_data = match_resp.json()

    # 2. Skill Gap
    sg_resp = client.post("/jobs/skill-gap", json={
        "candidate": candidate_payload,
        "job": job_payload,
        "jd_analysis": jd_payload,
        "match_result": match_data
    })
    assert sg_resp.status_code == 200
    sg_data = sg_resp.json()
    assert "Spark" in sg_data["critical_gaps"]
    assert "AWS" in sg_data["secondary_gaps"]


# 13. Demo mode match + skill gap
def test_demo_mode_match_and_skill_gap():
    job_payload = {
        "id": "demo_job_python_dev",
        "job_id": "demo_job_python_dev",
        "title": "Python Developer",
        "company": "DemoCorp",
        "location": "Indore",
        "is_demo": True,
        "canonical_url": "http://democorp.com/jobs/python"
    }
    match_resp = client.post("/jobs/match", json={
        "candidate": {"name": "Demo User", "skills": ["Python"]},
        "job": job_payload,
        "jd_analysis": None
    })
    assert match_resp.status_code == 200

    sg_resp = client.post("/jobs/skill-gap", json={
        "candidate": {"name": "Demo User", "skills": ["Python"]},
        "job": job_payload,
        "jd_analysis": None,
        "match_result": match_resp.json()
    })
    assert sg_resp.status_code == 200


# 14. Real mode path (Mocks external search & analyzer)
def test_real_mode_path():
    with patch("app.services.jd_analyzer.GroqJDAnalyzer.analyze_jd") as mock_analyze:
        mock_analyze.return_value = JDAnalysis(
            job_id="job_real_1",
            title="Senior Python Backend Dev",
            required_skills=["Python", "FastAPI", "PostgreSQL"],
            preferred_skills=["Docker"]
        )
        
        analyze_resp = client.post("/jobs/jd/analyze", json={
            "job_id": "job_real_1",
            "canonical_url": "http://realtech.com/jobs/1",
            "raw_jd_text": "Seeking Senior Python Backend Dev with FastAPI and PostgreSQL..."
        })
        assert analyze_resp.status_code == 200
        jd_analysis = analyze_resp.json()
        assert "FastAPI" in jd_analysis["required_skills"]


# 15. Existing cached records remain compatible
def test_existing_cached_records_compatibility():
    repo = JDCacheRepository()
    # Insert old-style record with missing optional fields
    old_record_json = json.dumps({
        "job_id": "job_old_1",
        "title": "Legacy System Developer",
        "required_skills": ["COBOL", "C"]
    })
    with get_db_connection() as db:
        db.execute(
            "INSERT OR REPLACE INTO jd_cache (job_id, raw_jd_text, jd_analysis_json, extracted_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            ("job_old_1", "Raw text legacy", old_record_json)
        )
    cached = repo.get_jd_analysis(job_id="job_old_1")
    assert cached is not None
    assert cached.job_id == "job_old_1"
    assert cached.required_skills == ["COBOL", "C"]
    assert cached.preferred_skills == []

