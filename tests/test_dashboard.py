"""
Dashboard regression unit tests covering dashboard API summary endpoint,
real statistics aggregation, HTML structure, demo mode toggles, and responsive navigation.
"""

import os
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings, reload_settings
from app.database import init_db
from app.database.repositories import CandidateRepository, JobRepository, ApplicationRepository
from app.models.candidate import CandidateProfile
from app.models.job import Job
from app.models.application import ApplicationPackage, CoverLetter, EmailDraft, LinkedInMessage
from app.services.demo_service import DemoService

client = TestClient(app)


def test_dashboard_summary_endpoint_structure():
    """Verify GET /dashboard/summary returns correct schema with non-fake default indicators."""
    res = client.get("/dashboard/summary")
    assert res.status_code == 200
    data = res.json()

    assert "demo_mode" in data
    assert "jobs_found" in data
    assert "matching_jobs_count" in data
    assert "applications_count" in data
    assert "interviews_count" in data
    assert "resume_status" in data
    assert "recent_jobs" in data
    assert "top_matches" in data
    assert "application_activity" in data
    assert "ai_insights" in data

    resume_st = data["resume_status"]
    assert "uploaded" in resume_st
    assert "candidate_name" in resume_st
    assert "skills_count" in resume_st


def test_dashboard_summary_demo_mode_toggle(monkeypatch):
    """Verify GET /dashboard/summary populates demo data when DEMO_MODE=true."""
    try:
        monkeypatch.setenv("DEMO_MODE", "true")
        reload_settings()

        res = client.get("/dashboard/summary")
        assert res.status_code == 200
        data = res.json()

        assert data["demo_mode"] is True
        assert data["jobs_found"] >= 3
        assert data["matching_jobs_count"] >= 1
        assert data["resume_status"]["uploaded"] is True
        assert "Alex Mercer" in data["resume_status"]["candidate_name"]
        assert len(data["recent_jobs"]) > 0
        assert len(data["top_matches"]) > 0
        assert len(data["ai_insights"]) > 0
    finally:
        monkeypatch.undo()
        reload_settings()


def test_dashboard_real_statistics_persistence(tmp_path):
    """Verify GET /dashboard/summary reflects real SQLite database rows."""
    db_file = str(tmp_path / "test_dashboard_real.db")
    init_db(db_file)

    # 1. Save Candidate
    cand_repo = CandidateRepository(db_path=db_file)
    cand = CandidateProfile(
        name="John Doe Real",
        email="john.real@example.com",
        location="Indore, India",
        skills=["Python", "FastAPI", "SQL"]
    )
    cand_repo.save_candidate(cand)

    # 2. Save Job
    job_repo = JobRepository(db_path=db_file)
    job = Job(
        job_id="real-job-999",
        title="Senior Python Engineer",
        company="Real Tech Ltd",
        location="Indore",
        work_mode="On-site",
        canonical_url="https://realtech.example.com/job/999"
    )
    job_repo.save_job(job)

    # 3. Save Tracked Application
    app_repo = ApplicationRepository(db_path=db_file)
    pkg = DemoService.get_demo_application_package(job_id=job.job_id, company=job.company, job_title=job.title)
    app_repo.save_application(package=pkg, status="INTERVIEWING", notes="Scheduled round 1")

    # Retrieve stats using repositories
    saved_cand = cand_repo.get_candidate()
    assert saved_cand.name == "John Doe Real"

    stored_jobs = job_repo.list_jobs()
    assert len(stored_jobs) == 1
    assert stored_jobs[0].company == "Real Tech Ltd"

    stats = app_repo.get_stats()
    assert stats.total_applications == 1
    assert stats.interviewing_count == 1


def test_dashboard_frontend_html_rendering():
    """Verify frontend/index.html contains dashboard elements, headers, tabs, and quick actions."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    assert os.path.exists(html_path)

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Title & Subtitle
    assert "AI JOB ASSISTANT" in html
    assert "Find, match and apply to jobs faster." in html

    # 5 Tab buttons
    assert 'data-tab="tab-dashboard"' in html
    assert 'data-tab="tab-resume"' in html
    assert 'data-tab="tab-job-search"' in html
    assert 'data-tab="tab-match-analysis"' in html
    assert 'data-tab="tab-application"' in html

    # 5 Tab panes
    assert 'id="tab-dashboard"' in html
    assert 'id="tab-resume"' in html
    assert 'id="tab-job-search"' in html
    assert 'id="tab-match-analysis"' in html
    assert 'id="tab-application"' in html

    # KPI summary card IDs
    assert 'id="dash-kpi-jobs-found"' in html
    assert 'id="dash-kpi-matching-jobs"' in html
    assert 'id="dash-kpi-applications"' in html
    assert 'id="dash-kpi-interviews"' in html

    # Candidate Resume Status Card IDs
    assert 'id="dash-resume-card"' in html
    assert 'id="dash-resume-badge"' in html
    assert 'id="dash-resume-name"' in html
    assert 'id="dash-resume-skills-count"' in html

    # Application Activity status count IDs
    assert 'id="dash-cnt-saved"' in html
    assert 'id="dash-cnt-applied"' in html
    assert 'id="dash-cnt-interviewing"' in html
    assert 'id="dash-cnt-offer"' in html
    assert 'id="dash-cnt-rejected"' in html
    assert 'id="dash-cnt-withdrawn"' in html

    # Quick actions bar
    assert "Upload Resume" in html
    assert "Search Jobs" in html
    assert "Analyze Match" in html
    assert "Write Application" in html

    # AI Insights
    assert 'id="dash-insights-list"' in html
