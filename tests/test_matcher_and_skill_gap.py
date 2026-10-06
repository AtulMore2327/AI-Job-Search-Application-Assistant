import pytest
from app.models.candidate import CandidateProfile, EducationItem, ProjectItem
from app.models.job import JobPosting, JobSearchPreferences
from app.services.matcher import ResumeJDMatcher
from app.services.skill_gap import SkillGapAnalyzer

def test_deterministic_scoring_and_skill_gap():
    candidate = CandidateProfile(
        name="Atul Deepak More",
        skills=["Python", "SQL", "Pandas", "Feature Engineering"],
        tools=["Power BI", "Tableau", "Looker Studio"],
        education=[EducationItem(degree="B.Sc. (Data Science)", institution="Devi Ahilya Vishwavidyalaya")],
        projects=[ProjectItem(title="Airbnb Data Analysis", description="Power BI analytics", technologies=["Power BI"])]
    )

    job = JobPosting(
        job_id="job123",
        title="Data Analyst",
        company="Apex Analytics",
        location="Surat",
        work_mode="On-site",
        required_skills=["Python", "SQL", "Power BI"],
        preferred_skills=["Tableau", "AWS"]
    )

    prefs = JobSearchPreferences(
        target_role="Data Analyst",
        location="Surat",
        experience_level="Fresher",
        work_mode="On-site"
    )

    match_result = ResumeJDMatcher.filter_and_match_job(candidate, job, prefs)
    
    assert match_result.is_preference_match is True
    assert match_result.match_score > 70.0
    assert "Python" in match_result.skill_gap.matched_skills
    assert "SQL" in match_result.skill_gap.matched_skills
    assert "AWS" in match_result.skill_gap.missing_nice_to_have
