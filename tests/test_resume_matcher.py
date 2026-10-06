"""
Unit tests for ResumeMatcherService, skill normalization, experience/education evaluation,
and deterministic scoring (Phase 8).
"""

from app.models.candidate import CandidateProfile, EducationItem, ExperienceItem
from app.models.job import Job, JDAnalysis
from app.models.preferences import UserPreferences
from app.services.resume_matcher import ResumeMatcherService, normalize_skill


def test_skill_normalization_utility():
    assert normalize_skill("Python Programming") == "python"
    assert normalize_skill("Python3") == "python"
    assert normalize_skill("Postgres") == "postgresql"
    assert normalize_skill("Power-BI") == "power bi"
    assert normalize_skill("MS Excel") == "excel"
    assert normalize_skill("ReactJS") == "react"
    assert normalize_skill("Node.js") == "node.js"
    assert normalize_skill("scikit-learn") == "scikit-learn"


def test_exact_and_normalized_skill_matching():
    candidate = CandidateProfile(
        name="Alex Smith",
        skills=["Python Programming", "Postgres", "Power-BI"],
        tools=["Git", "Docker"]
    )
    job = Job(
        job_id="job_skill_1",
        title="Data Engineer",
        company="Data Corp",
        canonical_url="https://example.com/job/1"
    )
    jd_analysis = JDAnalysis(
        job_id="job_skill_1",
        required_skills=["python", "postgresql", "power bi", "tableau"],
        preferred_skills=["docker", "aws"]
    )

    matcher = ResumeMatcherService()
    res = matcher.match_candidate_to_job(candidate, job, jd_analysis)

    assert "python" in [s.lower() for s in res.matched_required_skills]
    assert "postgresql" in [s.lower() for s in res.matched_required_skills]
    assert "power bi" in [s.lower() for s in res.matched_required_skills]
    assert "tableau" in [s.lower() for s in res.missing_required_skills]
    assert "docker" in [s.lower() for s in res.matched_preferred_skills]
    assert "aws" in [s.lower() for s in res.missing_preferred_skills]


def test_partial_skill_matching():
    candidate = CandidateProfile(
        name="Sam Taylor",
        skills=["Machine Learning", "Power BI"]
    )
    job = Job(job_id="job_partial", title="ML Dev", company="AI Tech", canonical_url="https://example.com/job/p")
    jd_analysis = JDAnalysis(
        job_id="job_partial",
        required_skills=["Machine Learning with scikit-learn", "Power BI dashboards"]
    )

    matcher = ResumeMatcherService()
    res = matcher.match_candidate_to_job(candidate, job, jd_analysis)

    assert len(res.partial_matches) > 0
    p_skills = [p["skill"] for p in res.partial_matches]
    assert any("Machine Learning" in s for s in p_skills) or any("Power BI" in s for s in p_skills)


def test_experience_evaluation():
    matcher = ResumeMatcherService()

    # Fresher requirement
    cand_fresher = CandidateProfile(name="Fresher Alex", experience=[])
    job = Job(job_id="job_exp", title="Data Analyst", company="Corp", canonical_url="https://example.com/j")
    jd_fresher = JDAnalysis(job_id="job_exp", experience_requirements="Fresher or 0-1 years")
    res_fresher = matcher.match_candidate_to_job(cand_fresher, job, jd_fresher)
    assert res_fresher.experience_match["status"] == "passed"

    # Senior requirement with low candidate experience
    cand_1yr = CandidateProfile(name="Junior Alex", experience=[ExperienceItem(title="Intern", company="Co")])
    jd_senior = JDAnalysis(job_id="job_exp", experience_requirements="5+ years of data engineering experience")
    res_senior = matcher.match_candidate_to_job(cand_1yr, job, jd_senior)
    assert res_senior.experience_match["status"] == "failed"


def test_education_evaluation():
    matcher = ResumeMatcherService()

    cand_btech = CandidateProfile(
        name="Engineer Alex",
        education=[EducationItem(degree="B.Tech in Computer Science")]
    )
    job = Job(job_id="job_edu", title="Software Dev", company="Corp", canonical_url="https://example.com/j")
    
    jd_bach = JDAnalysis(job_id="job_edu", education_requirements="Any bachelor's degree in CS or IT")
    res_bach = matcher.match_candidate_to_job(cand_btech, job, jd_bach)
    assert res_bach.education_match["status"] == "passed"

    jd_masters = JDAnalysis(job_id="job_edu", education_requirements="Master's degree or PhD in AI")
    res_masters = matcher.match_candidate_to_job(cand_btech, job, jd_masters)
    assert res_masters.education_match["status"] == "failed"


def test_deterministic_score_reproducibility_and_weighting():
    candidate = CandidateProfile(
        name="Jordan",
        skills=["Python", "SQL", "Power BI"],
        education=[EducationItem(degree="B.Sc in Data Science")],
        experience=[ExperienceItem(title="Data Analyst", company="Analytica")]
    )
    job = Job(
        job_id="job_det",
        title="Data Analyst",
        company="Analytica",
        location="Surat",
        work_mode="Hybrid",
        employment_type="Full-time",
        canonical_url="https://example.com/j"
    )
    jd = JDAnalysis(
        job_id="job_det",
        required_skills=["Python", "SQL"],
        preferred_skills=["Power BI"],
        experience_requirements="1 year",
        education_requirements="Bachelor's degree"
    )
    prefs = UserPreferences(target_role="Data Analyst", location="Surat", work_mode="Hybrid")

    matcher = ResumeMatcherService()
    res1 = matcher.match_candidate_to_job(candidate, job, jd, prefs)
    res2 = matcher.match_candidate_to_job(candidate, job, jd, prefs)

    # Deterministic reproducibility check
    assert res1.match_score == res2.match_score
    assert res1.score_breakdown == res2.score_breakdown
    assert res1.match_score >= 80.0  # High fit candidate

    # Required skills weight check (40%) > Preferred skills weight (15%)
    assert res1.score_breakdown["required_skills"] == 40.0
    assert res1.score_breakdown["preferred_skills"] == 15.0
