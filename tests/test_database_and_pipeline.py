import pytest
from app.models.job import JobSearchPreferences
from app.services.orchestrator import orchestrator
from app.database.repositories import DatabaseRepository

def test_full_pipeline_execution():
    prefs = JobSearchPreferences(
        target_role="Data Analyst",
        location="Surat",
        experience_level="Fresher",
        work_mode="On-site",
        result_limit=5
    )
    sample_resume = "Atul Deepak More. Skills: Python, SQL, Power BI, Looker Studio. Experience in EDA and visualization."

    results = orchestrator.run_pipeline(sample_resume, prefs, is_pdf=False)
    
    assert "statistics" in results
    assert results["statistics"]["unique_jobs_count"] > 0
    assert len(results["jobs"]) > 0
    assert len(results["match_results"]) > 0

    # Check database persistence
    saved_apps = DatabaseRepository.get_all_applications()
    assert len(saved_apps) > 0
