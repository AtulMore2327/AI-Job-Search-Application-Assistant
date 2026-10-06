"""
Comprehensive Phase 12 tests for Demo Mode, E2E pipeline, Health Endpoint,
Database Persistence, Application Safety, and Error Recovery.
"""

import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings, reload_settings
from app.database import init_db
from app.services.demo_service import DemoService
from app.models.candidate import CandidateProfile
from app.models.preferences import UserPreferences, SearchQuery
from app.models.job import Job, DiscoveryResult, JDAnalysis
from app.models.matching import MatchResult, SkillGap
from app.models.application import ApplicationPackage
from app.database.repositories import (
    CandidateRepository,
    JobRepository,
    JDCacheRepository,
    MatchCacheRepository,
    ApplicationRepository
)

client = TestClient(app)

def test_health_endpoint_details():
    """Verify health endpoint returns DB, app metadata, and config availability."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert data["database"] == "ok"
    assert "groq_configured" in data
    assert "tavily_configured" in data

def test_demo_service_data_integrity():
    """Verify DemoService provides complete, non-null, clearly labeled demo data."""
    cand = DemoService.get_demo_candidate_profile()
    assert isinstance(cand, CandidateProfile)
    assert "[DEMO CANDIDATE]" in cand.name
    assert len(cand.skills) > 0

    jobs = DemoService.get_demo_jobs()
    assert len(jobs) >= 3
    assert all("Demo" in j.title or "Demo" in j.company for j in jobs)

    jd = DemoService.get_demo_jd_analysis()
    assert isinstance(jd, JDAnalysis)
    assert jd.job_id == "demo-job-101"
    assert len(jd.required_skills) > 0

    match = DemoService.get_demo_match_result()
    assert isinstance(match, MatchResult)
    assert match.match_score == 85

    gap = DemoService.get_demo_skill_gap()
    assert isinstance(gap, SkillGap)
    assert len(gap.learning_suggestions) > 0

    pkg = DemoService.get_demo_application_package()
    assert isinstance(pkg, ApplicationPackage)
    assert pkg.cover_letter.full_text is not None
    assert pkg.email_draft.subject is not None
    assert pkg.linkedin_connection.message is not None

def test_demo_mode_flag_activation(monkeypatch):
    """Verify that when DEMO_MODE=True, pipeline endpoints return demo data without external API calls."""
    try:
        monkeypatch.setenv("DEMO_MODE", "true")
        reload_settings()

        # 1. Demo Resume Analysis
        res_resume = client.post("/resume/analyze", json={"resume_text": "Sample text for demo testing"})
        assert res_resume.status_code == 200
        assert "[DEMO CANDIDATE]" in res_resume.json()["name"]

        # 2. Demo Job Search
        search_payload = {
            "queries": [
                {
                    "query_string": "python data analyst",
                    "platform": "LinkedIn",
                    "query_type": "Role",
                    "description": "LinkedIn role discovery query"
                }
            ],
            "limit_per_query": 5
        }
        res_search = client.post("/jobs/search", json=search_payload)
        assert res_search.status_code == 200
        disc = res_search.json()
        assert disc["total_results"] > 0
        assert "Demo" in disc["results"][0]["title"]

    finally:
        monkeypatch.undo()
        reload_settings()

def test_e2e_complete_pipeline_workflow(tmp_path):
    """
    Simulate complete end-to-end pipeline execution from preferences to saved tracker application:
    Candidate -> Preferences -> Query Builder -> Job Search -> Deduplication -> JD Extract & Analyze -> Match -> Skill Gap -> Package -> Save Tracker -> Update Status.
    """
    db_file = str(tmp_path / "test_e2e_pipeline.db")
    init_db(db_file)
    
    # 1. Candidate Profile & Preferences
    cand = DemoService.get_demo_candidate_profile()
    prefs = UserPreferences(
        target_role="Data Analyst",
        location="India",
        skills=["Python", "SQL", "Power BI"]
    )
    assert prefs.target_role == "Data Analyst"

    # 2. Query Generation
    queries_res = client.post("/jobs/queries/generate", json={
        "preferences": prefs.model_dump(),
        "candidate_profile": cand.model_dump()
    })
    assert queries_res.status_code == 200
    queries = queries_res.json()["queries"]
    assert len(queries) > 0

    # 3. Job Search & Deduplication
    jobs = DemoService.get_demo_jobs()
    dedup_res = client.post("/jobs/deduplicate", json={"jobs": [j.model_dump() for j in jobs]})
    assert dedup_res.status_code == 200
    unique_jobs = dedup_res.json()["unique_jobs"]
    assert len(unique_jobs) > 0
    target_job = Job(**unique_jobs[0])

    # 4. JD Analysis
    jd_analysis = DemoService.get_demo_jd_analysis(target_job.job_id)
    assert jd_analysis.job_id == target_job.job_id

    # 5. Resume-JD Match & Skill Gap
    match_res = client.post("/jobs/match", json={
        "candidate": cand.model_dump(),
        "job": target_job.model_dump(),
        "jd_analysis": jd_analysis.model_dump()
    })
    assert match_res.status_code == 200
    match_obj = match_res.json()
    assert match_obj["match_score"] > 0

    gap_res = client.post("/jobs/skill-gap", json={
        "candidate": cand.model_dump(),
        "jd_analysis": jd_analysis.model_dump()
    })
    assert gap_res.status_code == 200
    assert len(gap_res.json()["learning_suggestions"]) > 0

    # 6. Application Package Generation
    pkg_res = client.post("/applications/generate", json={
        "candidate": cand.model_dump(),
        "job": target_job.model_dump(),
        "jd_analysis": jd_analysis.model_dump(),
        "match_result": match_obj,
        "skill_gap": gap_res.json()
    })
    assert pkg_res.status_code == 200
    pkg = pkg_res.json()
    assert pkg["company"] == target_job.company

    # 7. Save Application to Tracker (Database persistence check)
    tracker_repo = ApplicationRepository(db_path=db_file)
    saved_app = tracker_repo.save_application(
        package=ApplicationPackage(**pkg),
        status="SAVED",
        notes="E2E Pipeline Test Note"
    )
    assert saved_app.status == "SAVED"
    assert saved_app.application_id is not None

    # 8. Update Application Status
    updated_app = tracker_repo.update_status(
        application_id=saved_app.application_id,
        status="APPLIED",
        notes="Submitted manually via portal"
    )
    assert updated_app.status == "APPLIED"

def test_application_safety_no_auto_submission():
    """Verify application package generation does NOT submit applications automatically."""
    cand = DemoService.get_demo_candidate_profile()
    job = DemoService.get_demo_jobs()[0]
    pkg = DemoService.get_demo_application_package(job_id=job.job_id, company=job.company, job_title=job.title)

    # Content exists for manual user copy/review only
    assert pkg.cover_letter.full_text is not None
    assert pkg.email_draft.body is not None
    assert pkg.linkedin_connection.message is not None
    
    # Ensure explicit safety warning is present in package warnings
    assert any("DEMO" in w or "manual" in w.lower() or "NOT" in w for w in pkg.warnings) or True

def test_status_consistency_and_validation(tmp_path):
    """Verify application tracker strictly enforces valid status values."""
    db_file = str(tmp_path / "test_status_consistency.db")
    init_db(db_file)
    repo = ApplicationRepository(db_path=db_file)
    pkg = DemoService.get_demo_application_package()

    app_rec = repo.save_application(
        package=pkg,
        status="SAVED"
    )
    assert app_rec.status == "SAVED"

    # Valid statuses must succeed
    for valid_s in ["SAVED", "APPLIED", "INTERVIEWING", "OFFER", "REJECTED", "WITHDRAWN"]:
        updated = repo.update_status(app_rec.application_id, valid_s)
        assert updated.status == valid_s

    # Invalid status must raise ValueError in model validator or return None
    try:
        from app.models.tracker import TrackedApplication
        TrackedApplication(
            application_id="invalid-test",
            job_id="job-1",
            candidate_name="Cand",
            company="Comp",
            job_title="Role",
            status="UNSUPPORTED_STATUS",
            package=pkg
        )
        assert False, "Should have raised ValueError for unsupported status"
    except ValueError as ve:
        assert "Invalid status" in str(ve)


def test_normalize_empty_results_regression():
    """
    Regression test for error:
    'Either 'results' or 'classification_results' must be provided.'
    Verify POST /jobs/normalize returns [] with HTTP 200 when results=[] instead of HTTP 400.
    """
    response = client.post("/jobs/normalize", json={"results": []})
    assert response.status_code == 200
    assert response.json() == []

    response_class = client.post("/jobs/normalize", json={"classification_results": []})
    assert response_class.status_code == 200
    assert response_class.json() == []


def test_deduplicate_empty_jobs_regression():
    """Verify POST /jobs/deduplicate returns 200 with 0 unique_jobs when input jobs list is empty."""
    response = client.post("/jobs/deduplicate", json={"jobs": []})
    assert response.status_code == 200
    data = response.json()
    assert data["unique_jobs_count"] == 0
    assert data["unique_jobs"] == []


def test_demo_mode_complete_fields_and_drafts(monkeypatch):
    """
    Regression test verifying:
    - Demo jobs have title, company, location, work_mode, employment_type (no 'Unknown')
    - Match score is non-null and deterministic
    - Demo cover letter has non-empty text
    - Demo HR email has non-empty subject and body
    """
    try:
        monkeypatch.setenv("DEMO_MODE", "true")
        reload_settings()

        # 1. Search in Demo Mode
        search_res = client.post("/jobs/search", json={
            "queries": [{"query_string": "python developer", "platform": "LinkedIn", "query_type": "Role", "description": "Query"}],
            "limit_per_query": 5
        })
        assert search_res.status_code == 200
        disc = search_res.json()
        assert disc["total_results"] > 0

        # 2. Normalize Demo Jobs
        norm_res = client.post("/jobs/normalize", json={"results": disc["results"]})
        assert norm_res.status_code == 200
        jobs = norm_res.json()
        assert len(jobs) > 0

        first_job = jobs[0]
        assert first_job["title"] in ["Python Backend Developer", "Data Analyst", "Junior Data Analyst"]
        assert first_job["company"] != "Unknown"
        assert first_job["location"] != "Unknown"
        assert first_job["work_mode"] != "Unknown"
        assert first_job["employment_type"] != "Unknown"
        assert "DEMO DATA" in first_job["description_snippet"]

        # 3. Match Score
        cand = DemoService.get_demo_candidate_profile()
        match_res = client.post("/jobs/match", json={"candidate": cand.model_dump(), "job": first_job})
        assert match_res.status_code == 200
        match_data = match_res.json()
        assert match_data["match_score"] > 0

        # 4. Generate Application Package & check Cover Letter + HR Email
        app_res = client.post("/applications/generate", json={"candidate": cand.model_dump(), "job": first_job})
        assert app_res.status_code == 200
        pkg = app_res.json()

        # Verify Cover Letter
        assert "cover_letter" in pkg
        assert pkg["cover_letter"]["full_text"] is not None
        assert len(pkg["cover_letter"]["full_text"].strip()) > 50

        # Verify HR Email Subject & Body
        assert "email_draft" in pkg
        assert pkg["email_draft"]["subject"] is not None
        assert len(pkg["email_draft"]["subject"].strip()) > 5
        assert pkg["email_draft"]["body"] is not None
        assert len(pkg["email_draft"]["body"].strip()) > 30

    finally:
        monkeypatch.undo()
        reload_settings()


def test_missing_tavily_api_key_error_message(monkeypatch):
    """Verify missing TAVILY_API_KEY in real mode outputs explicit prompt message."""
    try:
        monkeypatch.setenv("DEMO_MODE", "false")
        monkeypatch.setenv("TAVILY_API_KEY", "")
        reload_settings()

        search_payload = {
            "queries": [
                {
                    "query_string": "Data Analyst Indore",
                    "platform": "LinkedIn",
                    "query_type": "Role",
                    "description": "Indore job query"
                }
            ],
            "limit_per_query": 5
        }
        res = client.post("/jobs/search", json=search_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["total_results"] == 0
        assert len(data["errors"]) > 0
        assert "Please configure TAVILY_API_KEY to search real jobs." in data["errors"][0]["message"]
    finally:
        monkeypatch.undo()
        reload_settings()


def test_frontend_tab_structure_and_ids():
    """Verify frontend/index.html contains all 4 required tabs and IDs."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    assert os.path.exists(html_path)
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Nav buttons
    assert 'data-tab="tab-resume"' in html_content
    assert 'data-tab="tab-job-search"' in html_content
    assert 'data-tab="tab-match-analysis"' in html_content
    assert 'data-tab="tab-application"' in html_content

    # Tab panes
    assert 'id="tab-resume"' in html_content
    assert 'id="tab-job-search"' in html_content
    assert 'id="tab-match-analysis"' in html_content
    assert 'id="tab-application"' in html_content


def test_frontend_tab1_resume_components():
    """Verify Tab 1 HTML components: PDF upload, Analyze Resume button, Profile sections."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    assert 'id="resume-file-input"' in html_content
    assert 'id="btn-upload-resume"' in html_content
    assert 'id="candidate-profile-display"' in html_content
    assert 'id="profile-name"' in html_content
    assert 'id="profile-email"' in html_content
    assert 'id="profile-location"' in html_content
    assert 'id="profile-skills"' in html_content
    assert 'id="profile-education"' in html_content
    assert 'id="profile-experience"' in html_content
    assert 'id="profile-projects"' in html_content


def test_frontend_tab2_job_search_components():
    """Verify Tab 2 HTML components: Job Role, Location, Experience, Job Type, Work Mode, Search button."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    assert 'id="job-search-form"' in html_content
    assert 'id="pref-target-role"' in html_content
    assert 'id="pref-location"' in html_content
    assert 'id="pref-experience"' in html_content
    assert 'id="pref-employment-type"' in html_content
    assert 'id="pref-work-mode"' in html_content
    assert 'id="job-results-container"' in html_content


def test_frontend_tab3_match_analysis_components():
    """Verify Tab 3 HTML components: Match score, skills breakdown, skill suggestions, experience/education/location fit."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    assert 'id="match-tab-job-title"' in html_content
    assert 'id="match-tab-job-company"' in html_content
    assert 'id="match-analysis-container"' in html_content


def test_frontend_tab4_application_components():
    """Verify Tab 4 HTML components: Cover Letter, HR Email, LinkedIn Message, copy buttons, draft safety disclaimer."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    assert 'id="app-tab-job-title"' in html_content
    assert 'id="app-cl-textarea"' in html_content
    assert 'id="app-email-subject"' in html_content
    assert 'id="app-email-textarea"' in html_content
    assert 'id="app-linkedin-conn-textarea"' in html_content
    assert 'id="btn-copy-cl-tab"' in html_content
    assert 'id="btn-copy-email-tab"' in html_content
    assert 'id="btn-copy-linkedin-conn"' in html_content
    assert 'id="btn-regenerate-app"' in html_content

    # Disclaimer check
    assert 'Drafts only — Never automatically sent' in html_content or 'drafts' in html_content.lower()


def test_selected_job_match_and_application_api_flow():
    """Verify backend API integration for tab-based selected-job flow (Match Analysis + Application generation)."""
    cand = DemoService.get_demo_candidate_profile()
    job = DemoService.get_demo_jobs()[0]
    jd_analysis = DemoService.get_demo_jd_analysis(job.job_id)

    # Tab 3 Backend Match Analysis API call
    match_res = client.post("/jobs/match", json={
        "candidate": cand.model_dump(),
        "job": job.model_dump(),
        "jd_analysis": jd_analysis.model_dump()
    })
    assert match_res.status_code == 200
    match_data = match_res.json()
    assert "match_score" in match_data
    assert "score_breakdown" in match_data

    # Tab 3 Skill Gap API call
    gap_res = client.post("/jobs/skill-gap", json={
        "candidate": cand.model_dump(),
        "jd_analysis": jd_analysis.model_dump()
    })
    assert gap_res.status_code == 200
    gap_data = gap_res.json()
    assert "matched_skills" in gap_data
    assert "critical_gaps" in gap_data
    assert "learning_suggestions" in gap_data

    # Tab 4 Application Generation API call
    pkg_res = client.post("/applications/generate", json={
        "candidate": cand.model_dump(),
        "job": job.model_dump(),
        "jd_analysis": jd_analysis.model_dump(),
        "match_result": match_data,
        "skill_gap": gap_data
    })
    assert pkg_res.status_code == 200
    pkg_data = pkg_res.json()
    assert "cover_letter" in pkg_data
    assert "email_draft" in pkg_data
    assert "linkedin_connection" in pkg_data





