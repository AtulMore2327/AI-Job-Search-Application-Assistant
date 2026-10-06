"""
Unit tests for SkillGapService (Phase 8).
"""

from app.models.candidate import CandidateProfile
from app.models.job import JDAnalysis
from app.services.skill_gap import SkillGapService


def test_skill_gap_critical_secondary_and_suggestions():
    candidate = CandidateProfile(
        name="Alex",
        skills=["Python", "SQL"]
    )
    jd_analysis = JDAnalysis(
        job_id="job_gap_1",
        required_skills=["Python", "SQL", "Tableau"],
        preferred_skills=["AWS", "Snowflake"]
    )

    gap_service = SkillGapService()
    gap = gap_service.analyze_gap(
        candidate=candidate,
        jd_analysis=jd_analysis,
        matched_required=["Python", "SQL"],
        missing_required=["Tableau"],
        matched_preferred=[],
        missing_preferred=["AWS", "Snowflake"],
        partial_matches=[]
    )

    assert "Tableau" in gap.critical_gaps
    assert "AWS" in gap.secondary_gaps
    assert "Snowflake" in gap.secondary_gaps
    assert "Python" in gap.matched_skills
    assert "SQL" in gap.matched_skills
    assert len(gap.learning_suggestions) >= 3
    assert any("Tableau" in s for s in gap.learning_suggestions)
    assert any("Completing these items improves technical alignment" in s for s in gap.learning_suggestions)


def test_skill_gap_no_gaps():
    candidate = CandidateProfile(
        name="Expert Alex",
        skills=["Python", "SQL", "Tableau", "AWS"]
    )
    jd_analysis = JDAnalysis(
        job_id="job_gap_2",
        required_skills=["Python", "SQL"],
        preferred_skills=["Tableau"]
    )

    gap_service = SkillGapService()
    gap = gap_service.analyze_gap(
        candidate=candidate,
        jd_analysis=jd_analysis,
        matched_required=["Python", "SQL"],
        missing_required=[],
        matched_preferred=["Tableau"],
        missing_preferred=[]
    )

    assert len(gap.critical_gaps) == 0
    assert len(gap.secondary_gaps) == 0
    assert any("Strong Alignment" in s for s in gap.learning_suggestions)
