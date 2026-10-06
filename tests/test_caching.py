"""
Unit tests for JD Analysis and Match Result Caching Layer (Phase 10).
"""

import pytest
from app.database.connection import init_db
from app.database.repositories import JDCacheRepository, MatchCacheRepository
from app.models.candidate import CandidateProfile
from app.models.job import Job, JDAnalysis
from app.models.matching import MatchResult, SkillGap
from app.services.jd_analyzer import GroqJDAnalyzer
from app.services.resume_matcher import ResumeMatcherService


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "cache_test.db"
    db_path = str(db_file)
    init_db(db_path)
    return db_path


def test_jd_analysis_cache_hit_and_miss(temp_db):
    repo = JDCacheRepository(temp_db)

    # Miss check
    assert repo.get_jd_analysis("job_c1") is None

    # Save to cache
    analysis = JDAnalysis(
        job_id="job_c1",
        title="Data Engineer",
        company="Cloud Data Inc",
        required_skills=["Python", "SQL"]
    )
    repo.save_jd_analysis(analysis, raw_jd_text="Clean JD text for Data Engineer")

    # Hit check
    cached = repo.get_jd_analysis("job_c1")
    assert cached is not None
    assert cached.title == "Data Engineer"
    assert "Python" in cached.required_skills


def test_groq_jd_analyzer_uses_cache(temp_db, monkeypatch):
    """Verify analyze_jd returns cached JDAnalysis without invoking Groq LLM on cache hit."""
    # Pre-populate cache
    repo = JDCacheRepository(temp_db)
    analysis = JDAnalysis(
        job_id="job_cached_100",
        title="Cached Title",
        company="Cached Company",
        required_skills=["Python"]
    )
    repo.save_jd_analysis(analysis, raw_jd_text="Sample JD")

    from app.config import reload_settings
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{temp_db}")
    reload_settings()

    analyzer = GroqJDAnalyzer(api_key="gsk_dummy")
    res = analyzer.analyze_jd("Sample JD", job_id="job_cached_100", use_cache=True)

    assert res.title == "Cached Title"
    assert res.company == "Cached Company"
    reload_settings()


def test_match_cache_hit_and_miss(temp_db):
    repo = MatchCacheRepository(temp_db)
    candidate = CandidateProfile(name="Alex", skills=["Python"])

    # Cache miss
    assert repo.get_match_result(candidate, "job_m1") is None

    # Save to cache
    match_res = MatchResult(
        job_id="job_m1",
        candidate_name="Alex",
        match_score=90.0,
        score_breakdown={"total": 90.0},
        matched_required_skills=["Python"],
        missing_required_skills=[],
        matched_preferred_skills=[],
        missing_preferred_skills=[],
        partial_matches=[],
        experience_match={"status": "passed", "reason": "ok"},
        education_match={"status": "passed", "reason": "ok"},
        location_match={"status": "passed", "reason": "ok"},
        work_mode_match={"status": "passed", "reason": "ok"},
        employment_type_match={"status": "passed", "reason": "ok"},
        strengths=["Strong fit"],
        concerns=[],
        skill_gap=SkillGap(matched_skills=["Python"]),
        explanation="Cached match result"
    )
    repo.save_match_result(candidate, "job_m1", match_res)

    # Cache hit
    cached = repo.get_match_result(candidate, "job_m1")
    assert cached is not None
    assert cached.match_score == 90.0
    assert cached.explanation == "Cached match result"
