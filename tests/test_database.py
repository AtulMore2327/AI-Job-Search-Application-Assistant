"""
Unit tests for SQLite Database connection, schemas, and Repositories (Phase 10).
"""

import pytest
from app.database.connection import init_db, resolve_db_path, get_db_connection
from app.database.repositories import (
    CandidateRepository,
    JobRepository,
    JDCacheRepository,
    MatchCacheRepository,
    ApplicationRepository
)
from app.models.candidate import CandidateProfile
from app.models.job import Job, JDAnalysis
from app.models.matching import MatchResult, SkillGap
from app.models.application import (
    ApplicationPackage,
    CoverLetter,
    EmailDraft,
    LinkedInMessage
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing temporary SQLite DB path and initializing schema."""
    db_file = tmp_path / "test_job_search.db"
    db_path = str(db_file)
    init_db(db_path)
    return db_path


def test_db_schema_initialization(temp_db):
    with get_db_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row["name"] for row in cursor.fetchall()]
        
        assert "candidates" in tables
        assert "jobs" in tables
        assert "jd_cache" in tables
        assert "match_cache" in tables
        assert "applications" in tables
        assert "user_preferences" in tables


def test_candidate_repository_crud(temp_db):
    repo = CandidateRepository(temp_db)
    cand = CandidateProfile(
        name="John Doe",
        email="john@example.com",
        skills=["Python", "SQL"]
    )
    
    saved = repo.save_candidate(cand, candidate_id="test_cand_1")
    assert saved.name == "John Doe"

    retrieved = repo.get_candidate("test_cand_1")
    assert retrieved is not None
    assert retrieved.name == "John Doe"
    assert "Python" in retrieved.skills


def test_job_repository_crud(temp_db):
    repo = JobRepository(temp_db)
    job1 = Job(job_id="j1", title="Data Analyst", company="Acme", canonical_url="https://example.com/j1")
    job2 = Job(job_id="j2", title="Backend Dev", company="Tech", canonical_url="https://example.com/j2")

    repo.save_jobs_batch([job1, job2])

    retrieved = repo.get_job("j1")
    assert retrieved is not None
    assert retrieved.company == "Acme"

    all_jobs = repo.list_jobs()
    assert len(all_jobs) == 2


def test_application_repository_status_transitions_and_stats(temp_db):
    repo = ApplicationRepository(temp_db)

    pkg = ApplicationPackage(
        job_id="job_app_99",
        candidate_name="Jane Doe",
        company="Global Corp",
        job_title="Software Engineer",
        cover_letter=CoverLetter(
            job_id="job_app_99",
            candidate_name="Jane Doe",
            company="Global Corp",
            job_title="Software Engineer",
            opening="Opening",
            body="Body",
            closing="Closing",
            signature="Signature",
            full_text="Full text"
        ),
        email_draft=EmailDraft(
            job_id="job_app_99",
            subject="Subj",
            body="Body",
            signature="Sig"
        ),
        linkedin_connection=LinkedInMessage(job_id="job_app_99", message="Msg", character_count=3, purpose="connection"),
        linkedin_recruiter=LinkedInMessage(job_id="job_app_99", message="Msg", character_count=3, purpose="recruiter_outreach"),
        linkedin_followup=LinkedInMessage(job_id="job_app_99", message="Msg", character_count=3, purpose="followup")
    )

    # 1. Save application (Initial status: SAVED)
    tracked = repo.save_application(pkg, status="SAVED", notes="Bookmark for review")
    assert tracked.application_id == "app_job_app_99"
    assert tracked.status == "SAVED"

    # 2. Status transition: SAVED -> APPLIED
    updated = repo.update_status("app_job_app_99", status="APPLIED", notes="Submitted via website")
    assert updated.status == "APPLIED"
    assert "Submitted" in updated.notes

    # 3. Status transition: APPLIED -> INTERVIEWING
    updated2 = repo.update_status("app_job_app_99", status="INTERVIEWING", notes="HR screening scheduled")
    assert updated2.status == "INTERVIEWING"

    # 4. List and filter by status
    interviewing_list = repo.list_applications(status_filter="INTERVIEWING")
    assert len(interviewing_list) == 1
    assert interviewing_list[0].job_title == "Software Engineer"

    # 5. Stats aggregation
    stats = repo.get_stats()
    assert stats.total_applications == 1
    assert stats.interviewing_count == 1

    # 6. Delete
    deleted = repo.delete_application("app_job_app_99")
    assert deleted is True
    assert repo.get_application("app_job_app_99") is None
