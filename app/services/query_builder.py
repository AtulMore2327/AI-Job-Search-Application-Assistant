from typing import List
from app.models.job import JobSearchPreferences
from app.models.candidate import CandidateProfile

class QueryBuilder:
    def __init__(self, preferences=None, candidate_profile=None):
        self.preferences = preferences
        self.candidate_profile = candidate_profile

    def build_queries(self):
        from app.models.preferences import SearchQuery
        prefs = self.preferences
        profile = self.candidate_profile
        
        target_role = getattr(prefs, 'target_role', 'Data Analyst') if prefs else 'Data Analyst'
        loc = getattr(prefs, 'location', 'Surat') if prefs else 'Surat'
        exp = getattr(prefs, 'experience_level', 'Fresher') if prefs else 'Fresher'
        pref_companies = getattr(prefs, 'preferred_companies', []) if prefs else []
        pref_skills = getattr(prefs, 'skills', []) if prefs else []
        
        queries = []
        
        # Base role & location query
        queries.append(SearchQuery(
            query_string=f'"{target_role}" "{loc}"',
            platform="General",
            query_type="Role",
            description="Base role and location search"
        ))
        
        # Boolean expanded query
        queries.append(SearchQuery(
            query_string=f'"{target_role}" "{loc}" ("BI Analyst" OR "Business Intelligence Analyst")',
            platform="General",
            query_type="BooleanExpanded",
            description="Expanded synonyms search"
        ))

        # Skill focused query
        skills_to_use = pref_skills or (profile.skills if profile else [])
        if skills_to_use:
            top_s = " ".join(skills_to_use[:3])
            queries.append(SearchQuery(
                query_string=f'"{target_role}" "{loc}" {top_s}',
                platform="General",
                query_type="SkillFocused",
                description="Skill focused search"
            ))

        # Company targeted query
        if pref_companies:
            comp_str = " OR ".join([f'"{c}"' for c in pref_companies])
            queries.append(SearchQuery(
                query_string=f'"{target_role}" "{loc}" ({comp_str})',
                platform="CompanyCareers",
                query_type="Company",
                description="Target company search"
            ))

        # Platform restricted queries
        platforms = ["LinkedIn", "Naukri", "Indeed", "Internshala", "CompanyCareers"]
        for p in platforms:
            queries.append(SearchQuery(
                query_string=f'"{target_role}" "{loc}" "{exp}"',
                platform=p,
                query_type="SiteRestricted",
                description=f"Platform search for {p}"
            ))

        return queries

    @staticmethod
    def build_search_queries(prefs: JobSearchPreferences, profile: CandidateProfile = None) -> List[str]:
        """
        Build dynamic multi-faceted search queries from job preferences and candidate profile.
        """
        queries = []
        role = prefs.target_role.strip() if prefs and getattr(prefs, 'target_role', None) else "Data Analyst"
        loc = prefs.location.strip() if prefs and getattr(prefs, 'location', None) else "Surat"
        exp = prefs.experience_level.strip() if prefs and getattr(prefs, 'experience_level', None) else "Fresher"
        mode = prefs.work_mode.strip() if prefs and getattr(prefs, 'work_mode', None) else "On-site"
        emp = prefs.employment_type.strip() if prefs and getattr(prefs, 'employment_type', None) else "Full-time"

        # Primary Targeted Query
        queries.append(f"{emp} {role} jobs in {loc} for {exp} candidates with {mode} work mode")

        # Platform-specific targeted string query
        queries.append(f"{role} {loc} {exp} vacancy LinkedIn Naukri Indeed Glassdoor Internshala")

        # Skill-enhanced Query if profile keywords exist
        if profile and profile.skills:
            top_skills = " ".join(profile.skills[:3])
            queries.append(f"{role} {loc} {top_skills} {exp}")

        # Company specific query if user has preferred companies
        pref_comps = getattr(prefs, 'preferred_companies', None)
        if pref_comps:
            comp_list = " OR ".join(pref_comps)
            queries.append(f"{role} {loc} ({comp_list})")

        return list(dict.fromkeys(queries))

SmartQueryBuilder = QueryBuilder
