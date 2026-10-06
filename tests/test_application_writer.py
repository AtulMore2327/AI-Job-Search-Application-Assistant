"""
Unit tests for ApplicationWriterService, ApplicationPackage models, anti-hallucination guarantees,
and deterministic fallback generation (Phase 9).
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from app.models.candidate import CandidateProfile, ProjectItem, EducationItem, ExperienceItem
from app.models.job import Job, JDAnalysis
from app.models.matching import MatchResult, SkillGap
from app.models.application import ApplicationPackage, CoverLetter, EmailDraft, LinkedInMessage
from app.services.application_writer import ApplicationWriterService


def test_application_writer_fallback_generation_success():
    candidate = CandidateProfile(
        name="Alex Smith",
        email="alex.smith@example.com",
        phone="+91 9876543210",
        skills=["Python", "SQL", "Power BI"],
        education=[EducationItem(degree="B.Tech in Computer Science")],
        experience=[ExperienceItem(title="Data Analyst Intern", company="Analytics Co")],
        projects=[ProjectItem(title="Customer Retention Analysis", technologies=["Python", "SQL"])]
    )
    job = Job(
        job_id="job_app_101",
        title="Data Analyst",
        company="Acme Solutions",
        canonical_url="https://example.com/job/app101"
    )
    jd_analysis = JDAnalysis(
        job_id="job_app_101",
        required_skills=["Python", "SQL"],
        preferred_skills=["Power BI"]
    )
    match_result = MatchResult(
        job_id="job_app_101",
        candidate_name="Alex Smith",
        match_score=85.0,
        score_breakdown={"total": 85.0},
        matched_required_skills=["Python", "SQL"],
        missing_required_skills=[],
        matched_preferred_skills=["Power BI"],
        missing_preferred_skills=[],
        partial_matches=[],
        experience_match={"status": "passed", "reason": "Fresh graduate fits 0-1 year entry level"},
        education_match={"status": "passed", "reason": "B.Tech degree matches requirement"},
        location_match={"status": "passed", "reason": "Location compatible"},
        work_mode_match={"status": "passed", "reason": "Hybrid mode matches"},
        employment_type_match={"status": "passed", "reason": "Full-time matches"},
        strengths=["Matched required skills: Python, SQL"],
        concerns=[],
        skill_gap=SkillGap(matched_skills=["Python", "SQL", "Power BI"]),
        explanation="High match score candidate."
    )

    writer = ApplicationWriterService(api_key="")  # Empty API key triggers fallback
    pkg = writer.generate_application_package(
        candidate=candidate,
        job=job,
        jd_analysis=jd_analysis,
        match_result=match_result
    )

    assert isinstance(pkg, ApplicationPackage)
    assert pkg.job_id == "job_app_101"
    assert pkg.candidate_name == "Alex Smith"
    assert pkg.company == "Acme Solutions"
    assert pkg.job_title == "Data Analyst"

    # Cover Letter checks
    assert "Alex Smith" in pkg.cover_letter.full_text
    assert "Acme Solutions" in pkg.cover_letter.full_text
    assert "Data Analyst" in pkg.cover_letter.full_text
    assert "Python" in pkg.cover_letter.full_text

    # Email Draft checks
    assert "Application for Data Analyst - Alex Smith" in pkg.email_draft.subject
    assert "Hiring Team" in pkg.email_draft.recipient_name
    assert "Alex Smith" in pkg.email_draft.signature

    # LinkedIn Messages checks
    assert pkg.linkedin_connection.purpose == "connection"
    assert pkg.linkedin_connection.character_count <= 300
    assert pkg.linkedin_recruiter.purpose == "recruiter_outreach"
    assert pkg.linkedin_followup.purpose == "followup"

    # Anti-hallucination check: missing skills are not claimed
    assert "Tableau" not in pkg.cover_letter.full_text


def test_application_writer_missing_skill_not_claimed():
    candidate = CandidateProfile(name="Jordan", skills=["Python", "SQL"])
    job = Job(job_id="job_gap", title="BI Dev", company="Tech Corp", canonical_url="https://example.com/j")
    jd = JDAnalysis(job_id="job_gap", required_skills=["Python", "Tableau"])
    skill_gap = SkillGap(critical_gaps=["Tableau"], matched_skills=["Python"])

    writer = ApplicationWriterService(api_key="")
    pkg = writer.generate_application_package(
        candidate=candidate,
        job=job,
        jd_analysis=jd,
        skill_gap=skill_gap
    )

    # Verify Tableau is NOT claimed as a candidate skill
    assert "I have strong Tableau experience" not in pkg.cover_letter.full_text
    assert "expert in Tableau" not in pkg.cover_letter.full_text


def test_application_writer_groq_mocked_success():
    candidate = CandidateProfile(name="Sam Taylor", email="sam@example.com", skills=["Python"])
    job = Job(job_id="job_groq", title="Python Dev", company="Cloud Systems", canonical_url="https://example.com/j")
    
    mock_llm_json = {
        "cover_letter": {
            "greeting": "Dear Hiring Manager,",
            "opening": "I am writing to apply for the Python Dev role at Cloud Systems.",
            "body": "I have verified experience developing applications in Python.",
            "closing": "Thank you for reviewing my application.",
            "signature": "Sincerely,\nSam Taylor",
            "full_text": "Dear Hiring Manager,\n\nI am writing to apply for the Python Dev role at Cloud Systems.\n\nSincerely,\nSam Taylor"
        },
        "email_draft": {
            "recipient_name": "Hiring Manager",
            "recipient_email": None,
            "subject": "Application for Python Dev - Sam Taylor",
            "body": "Hello Hiring Manager,\n\nPlease review my attached application for Python Dev.",
            "signature": "Best regards,\nSam Taylor"
        },
        "linkedin_connection": {
            "recipient_name": None,
            "message": "Hi, I am applying for the Python Dev position at Cloud Systems and would love to connect!",
            "purpose": "connection"
        },
        "linkedin_recruiter": {
            "recipient_name": None,
            "message": "Hello, I am interested in the Python Dev role at Cloud Systems. I bring proven Python experience.",
            "purpose": "recruiter_outreach"
        },
        "linkedin_followup": {
            "recipient_name": None,
            "message": "Hi, following up on my application for the Python Dev position at Cloud Systems.",
            "purpose": "followup"
        },
        "personalization_points": [
            "Matched core skill: Python",
            "Targeted company: Cloud Systems"
        ]
    }

    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=f"```json\n{json.dumps(mock_llm_json)}\n```"))
    ]

    mock_settings = MagicMock()
    mock_settings.GROQ_API_KEY = "gsk_mock_valid_key"

    with patch("app.services.application_writer.get_settings", return_value=mock_settings), \
         patch("groq.Groq") as mock_groq_class:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_groq_class.return_value = mock_instance

        writer = ApplicationWriterService()
        pkg = writer.generate_application_package(candidate=candidate, job=job)

        assert isinstance(pkg, ApplicationPackage)
        assert pkg.job_id == "job_groq"
        assert pkg.candidate_name == "Sam Taylor"
        assert pkg.cover_letter.greeting == "Dear Hiring Manager,"
        assert "Cloud Systems" in pkg.cover_letter.opening
        assert len(pkg.personalization_points) == 2
