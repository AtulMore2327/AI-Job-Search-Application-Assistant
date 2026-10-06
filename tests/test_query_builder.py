"""
Unit tests for UserPreferences Pydantic schema and SmartQueryBuilder service.
"""

import pytest
from app.models.preferences import UserPreferences, SearchQuery
from app.models.candidate import CandidateProfile
from app.services.query_builder import SmartQueryBuilder


def test_user_preferences_validation():
    # Valid preferences
    prefs = UserPreferences(
        target_role="Data Analyst",
        location="Surat",
        experience_level="Fresher",
        employment_type="Full-time",
        work_mode="Hybrid",
        salary_min=300000,
        salary_max=600000
    )
    assert prefs.target_role == "Data Analyst"
    assert prefs.location == "Surat"

    # Empty target role validation
    with pytest.raises(ValueError, match="target_role cannot be empty"):
        UserPreferences(target_role="")

    # Salary range validation (salary_max < salary_min)
    with pytest.raises(ValueError, match="salary_max cannot be less than salary_min"):
        UserPreferences(target_role="Data Analyst", salary_min=500000, salary_max=300000)


def test_query_builder_base_queries():
    prefs = UserPreferences(
        target_role="Data Analyst",
        location="Surat",
        work_mode="Any"
    )
    builder = SmartQueryBuilder(preferences=prefs)
    queries = builder.build_queries()
    
    assert len(queries) > 1
    query_strings = [q.query_string for q in queries]
    
    # Check base role & location query exists
    assert any('"Data Analyst" "Surat"' in q for q in query_strings)


def test_query_builder_work_mode_and_fresher():
    prefs = UserPreferences(
        target_role="Software Engineer",
        location="Remote",
        work_mode="Remote",
        experience_level="Fresher",
        employment_type="Full-time"
    )
    builder = SmartQueryBuilder(preferences=prefs)
    queries = builder.build_queries()
    
    query_strings = [q.query_string for q in queries]
    
    # Work mode targeted query
    assert any('"Software Engineer" "Remote"' in q for q in query_strings)
    # Fresher query
    assert any('"Fresher"' in q for q in query_strings)


def test_query_builder_with_candidate_profile_skills():
    prefs = UserPreferences(
        target_role="Data Analyst",
        location="Bangalore",
        skills=["Python", "SQL"]
    )
    profile = CandidateProfile(
        name="John Doe",
        skills=["PowerBI", "Tableau", "Pandas"]
    )
    
    builder = SmartQueryBuilder(preferences=prefs, candidate_profile=profile)
    queries = builder.build_queries()
    
    # Find skill-focused query
    skill_queries = [q for q in queries if q.query_type == "SkillFocused"]
    assert len(skill_queries) >= 1
    
    skill_q_str = skill_queries[0].query_string
    assert "Python" in skill_q_str or "PowerBI" in skill_q_str


def test_query_builder_company_targeted():
    prefs = UserPreferences(
        target_role="Data Analyst",
        location="Surat",
        preferred_companies=["ABC Technologies", "XYZ Solutions"]
    )
    builder = SmartQueryBuilder(preferences=prefs)
    queries = builder.build_queries()
    
    company_queries = [q for q in queries if q.query_type == "Company"]
    assert len(company_queries) == 1
    assert "ABC Technologies" in company_queries[0].query_string
    assert "XYZ Solutions" in company_queries[0].query_string


def test_query_builder_synonym_expansion():
    prefs = UserPreferences(
        target_role="Data Analyst",
        location="Surat"
    )
    builder = SmartQueryBuilder(preferences=prefs)
    queries = builder.build_queries()
    
    boolean_queries = [q for q in queries if q.query_type == "BooleanExpanded"]
    assert len(boolean_queries) == 1
    assert "BI Analyst" in boolean_queries[0].query_string or "Business Intelligence Analyst" in boolean_queries[0].query_string


def test_query_builder_site_restricted_platforms():
    prefs = UserPreferences(
        target_role="Data Analyst",
        location="Surat",
        experience_level="Fresher"
    )
    builder = SmartQueryBuilder(preferences=prefs)
    queries = builder.build_queries()
    
    platforms = {q.platform for q in queries}
    assert "LinkedIn" in platforms
    assert "Naukri" in platforms
    assert "Indeed" in platforms
    assert "Internshala" in platforms
    assert "CompanyCareers" in platforms
