"""
Unit tests for PreferenceFilterService (Phase 8).
"""

from app.models.job import Job, JDAnalysis
from app.models.preferences import UserPreferences
from app.services.preference_filter import PreferenceFilterService


def test_preference_filter_role_and_location_match():
    prefs = UserPreferences(
        target_role="Data Analyst",
        location="Surat",
        work_mode="Hybrid",
        employment_type="Full-time"
    )
    job = Job(
        job_id="job_001",
        title="Senior Data Analyst",
        company="Tech India",
        location="Surat",
        work_mode="Hybrid",
        employment_type="Full-time",
        canonical_url="https://example.com/job/001"
    )
    
    filter_service = PreferenceFilterService()
    res = filter_service.filter_job(prefs, job)
    
    assert res.job_id == "job_001"
    assert res.passed is True
    assert len(res.failed_criteria) == 0
    
    role_check = next(c for c in res.checks if c.criterion == "target_role")
    assert role_check.status == "passed"
    
    loc_check = next(c for c in res.checks if c.criterion == "location")
    assert loc_check.status == "passed"


def test_preference_filter_role_mismatch():
    prefs = UserPreferences(target_role="Graphic Designer")
    job = Job(
        job_id="job_002",
        title="DevOps Engineer",
        company="Cloud Ops",
        canonical_url="https://example.com/job/002"
    )
    
    filter_service = PreferenceFilterService()
    res = filter_service.filter_job(prefs, job)
    
    assert res.passed is False
    assert "target_role" in res.failed_criteria


def test_preference_filter_work_mode_remote_hybrid_onsite():
    prefs_remote = UserPreferences(target_role="Software Engineer", work_mode="Remote")
    job_remote = Job(
        job_id="job_r",
        title="Software Engineer",
        company="Global Inc",
        work_mode="Remote",
        canonical_url="https://example.com/job/r"
    )
    
    filter_service = PreferenceFilterService()
    res = filter_service.filter_job(prefs_remote, job_remote)
    assert res.passed is True
    
    job_onsite = Job(
        job_id="job_o",
        title="Software Engineer",
        company="Global Inc",
        work_mode="Onsite",
        canonical_url="https://example.com/job/o"
    )
    res_mismatch = filter_service.filter_job(prefs_remote, job_onsite)
    assert res_mismatch.passed is False
    assert "work_mode" in res_mismatch.failed_criteria


def test_preference_filter_salary_match_and_unknown():
    prefs = UserPreferences(target_role="Data Analyst", salary_min=400000, salary_max=800000)
    
    # Salary unknown
    job_no_salary = Job(
        job_id="job_nosal",
        title="Data Analyst",
        company="ABC Corp",
        canonical_url="https://example.com/job/nosal"
    )
    filter_service = PreferenceFilterService()
    res_unknown = filter_service.filter_job(prefs, job_no_salary)
    assert res_unknown.passed is True  # Unknown does NOT fail job
    sal_check = next(c for c in res_unknown.checks if c.criterion == "salary")
    assert sal_check.status == "unknown"

    # Salary matching
    job_with_sal = Job(
        job_id="job_sal",
        title="Data Analyst",
        company="ABC Corp",
        salary_min=500000,
        salary_max=700000,
        canonical_url="https://example.com/job/sal"
    )
    res_sal = filter_service.filter_job(prefs, job_with_sal)
    assert res_sal.passed is True
    assert next(c for c in res_sal.checks if c.criterion == "salary").status == "passed"


def test_preference_filter_preferred_company():
    prefs = UserPreferences(target_role="Data Analyst", preferred_companies=["Google", "Microsoft"])
    
    job_google = Job(
        job_id="job_g",
        title="Data Analyst",
        company="Google LLC",
        canonical_url="https://example.com/job/g"
    )
    filter_service = PreferenceFilterService()
    assert filter_service.filter_job(prefs, job_google).passed is True

    job_other = Job(
        job_id="job_oth",
        title="Data Analyst",
        company="Startup XYZ",
        canonical_url="https://example.com/job/oth"
    )
    assert filter_service.filter_job(prefs, job_other).passed is False
