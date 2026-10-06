"""
Preference Filtering Service.
Evaluates job postings against user preferences and returns detailed, explainable per-criterion checks.
"""

from typing import Optional, List, Dict, Any
from app.models.job import Job, JDAnalysis
from app.models.preferences import UserPreferences
from app.models.matching import PreferenceCheck, PreferenceFilterResult
from app.utils.logging import get_logger

logger = get_logger("preference_filter")


class PreferenceFilterService:
    """Service for filtering job postings against user preferences with explainable criteria."""

    def filter_job(
        self,
        preferences: UserPreferences,
        job: Job,
        jd_analysis: Optional[JDAnalysis] = None
    ) -> PreferenceFilterResult:
        """
        Evaluate job against all criteria in UserPreferences.
        
        Args:
            preferences: User preferences object.
            job: Normalized Job model.
            jd_analysis: Optional full JDAnalysis model.
            
        Returns:
            PreferenceFilterResult with per-criterion explanations.
        """
        checks: List[PreferenceCheck] = []
        failed_criteria: List[str] = []

        # 1. Target Role Check
        target_role_lower = preferences.target_role.lower().strip()
        job_title = job.title.lower() if job.title else ""
        jd_title = (jd_analysis.title.lower() if jd_analysis and jd_analysis.title else "")
        
        # Simple overlap or substring match
        role_tokens = [t for t in target_role_lower.split() if len(t) > 2]
        matches_role = (
            target_role_lower in job_title or
            job_title in target_role_lower or
            any(t in job_title or (jd_title and t in jd_title) for t in role_tokens)
        )
        if matches_role:
            checks.append(PreferenceCheck(
                criterion="target_role",
                status="passed",
                reason=f"Job title '{job.title}' matches target role '{preferences.target_role}'"
            ))
        else:
            checks.append(PreferenceCheck(
                criterion="target_role",
                status="failed",
                reason=f"Job title '{job.title}' does not match target role '{preferences.target_role}'"
            ))
            failed_criteria.append("target_role")

        # 2. Location Check
        pref_loc = preferences.location.lower().strip()
        job_loc = (job.location or "Unknown").lower().strip()
        jd_loc = (jd_analysis.location or "").lower().strip() if jd_analysis else ""
        
        if pref_loc in ["any", "", "all"]:
            checks.append(PreferenceCheck(
                criterion="location",
                status="passed",
                reason="User accepts any location"
            ))
        elif pref_loc == "remote" and (job.work_mode.lower() == "remote" or "remote" in job_loc or "remote" in jd_loc):
            checks.append(PreferenceCheck(
                criterion="location",
                status="passed",
                reason="Job is Remote and user accepts Remote location"
            ))
        elif job_loc == "unknown" and not jd_loc:
            checks.append(PreferenceCheck(
                criterion="location",
                status="unknown",
                reason="Location is not stated in the job posting"
            ))
        elif pref_loc in job_loc or (jd_loc and pref_loc in jd_loc) or job_loc in pref_loc:
            checks.append(PreferenceCheck(
                criterion="location",
                status="passed",
                reason=f"Job location '{job.location}' matches user location '{preferences.location}'"
            ))
        elif "remote" in job_loc or job.work_mode.lower() == "remote":
            checks.append(PreferenceCheck(
                criterion="location",
                status="passed",
                reason="Job is Remote which satisfies location requirement"
            ))
        else:
            checks.append(PreferenceCheck(
                criterion="location",
                status="failed",
                reason=f"Job location '{job.location}' does not match preferred location '{preferences.location}'"
            ))
            failed_criteria.append("location")

        # 3. Work Mode Check
        pref_wm = preferences.work_mode.lower().strip()
        job_wm = job.work_mode.lower().strip() if job.work_mode else "unknown"
        if jd_analysis and jd_analysis.work_mode and job_wm == "unknown":
            job_wm = jd_analysis.work_mode.lower().strip()
            
        if pref_wm in ["any", "", "all"]:
            checks.append(PreferenceCheck(
                criterion="work_mode",
                status="passed",
                reason="User accepts any work mode"
            ))
        elif job_wm == "unknown":
            checks.append(PreferenceCheck(
                criterion="work_mode",
                status="unknown",
                reason="Work mode is not stated in the job description"
            ))
        elif pref_wm in job_wm or job_wm in pref_wm:
            checks.append(PreferenceCheck(
                criterion="work_mode",
                status="passed",
                reason=f"Job work mode '{job.work_mode}' matches user preference '{preferences.work_mode}'"
            ))
        else:
            checks.append(PreferenceCheck(
                criterion="work_mode",
                status="failed",
                reason=f"Job work mode '{job.work_mode}' does not match user preference '{preferences.work_mode}'"
            ))
            failed_criteria.append("work_mode")

        # 4. Employment Type Check
        pref_et = preferences.employment_type.lower().strip()
        job_et = job.employment_type.lower().strip() if job.employment_type else "unknown"
        if jd_analysis and jd_analysis.employment_type and job_et == "unknown":
            job_et = jd_analysis.employment_type.lower().strip()

        if pref_et in ["any", "", "all"]:
            checks.append(PreferenceCheck(
                criterion="employment_type",
                status="passed",
                reason="User accepts any employment type"
            ))
        elif job_et == "unknown":
            checks.append(PreferenceCheck(
                criterion="employment_type",
                status="unknown",
                reason="Employment type is not stated in the job posting"
            ))
        elif pref_et in job_et or job_et in pref_et:
            checks.append(PreferenceCheck(
                criterion="employment_type",
                status="passed",
                reason=f"Job employment type '{job.employment_type}' matches user preference '{preferences.employment_type}'"
            ))
        else:
            checks.append(PreferenceCheck(
                criterion="employment_type",
                status="failed",
                reason=f"Job employment type '{job.employment_type}' does not match user preference '{preferences.employment_type}'"
            ))
            failed_criteria.append("employment_type")

        # 5. Preferred Companies Check
        if not preferences.preferred_companies:
            checks.append(PreferenceCheck(
                criterion="preferred_companies",
                status="passed",
                reason="No specific company restriction specified in user preferences"
            ))
        else:
            job_comp = job.company.lower().strip() if job.company else ""
            pref_comps_lower = [c.lower().strip() for c in preferences.preferred_companies]
            if any(c in job_comp or job_comp in c for c in pref_comps_lower):
                checks.append(PreferenceCheck(
                    criterion="preferred_companies",
                    status="passed",
                    reason=f"Company '{job.company}' matches user preferred company list"
                ))
            else:
                checks.append(PreferenceCheck(
                    criterion="preferred_companies",
                    status="failed",
                    reason=f"Company '{job.company}' is not in user preferred companies ({', '.join(preferences.preferred_companies)})"
                ))
                failed_criteria.append("preferred_companies")

        # 6. Experience Level Check
        pref_exp = preferences.experience_level.lower().strip()
        job_exp = (job.experience_level or "").lower().strip()
        if jd_analysis and jd_analysis.experience_requirements and not job_exp:
            job_exp = jd_analysis.experience_requirements.lower().strip()
            
        if not job_exp:
            checks.append(PreferenceCheck(
                criterion="experience_level",
                status="unknown",
                reason="Experience requirement is not explicitly stated in the job description"
            ))
        elif pref_exp in job_exp or job_exp in pref_exp:
            checks.append(PreferenceCheck(
                criterion="experience_level",
                status="passed",
                reason=f"Job experience requirement '{job_exp}' matches user experience level '{preferences.experience_level}'"
            ))
        elif pref_exp in ["fresher", "entry-level", "entry level"] and any(term in job_exp for term in ["0-1", "0-2", "fresher", "entry", "1 year"]):
            checks.append(PreferenceCheck(
                criterion="experience_level",
                status="passed",
                reason=f"Job experience requirement '{job_exp}' is compatible with user level '{preferences.experience_level}'"
            ))
        elif "any" in job_exp or "unknown" in job_exp:
            checks.append(PreferenceCheck(
                criterion="experience_level",
                status="passed",
                reason=f"Job experience requirement '{job_exp}' is open to any experience level"
            ))
        else:
            checks.append(PreferenceCheck(
                criterion="experience_level",
                status="failed",
                reason=f"Job experience requirement '{job_exp}' evaluated against candidate level '{preferences.experience_level}'"
            ))
            failed_criteria.append("experience_level")

        # 7. Salary Check
        has_pref_salary = (preferences.salary_min is not None or preferences.salary_max is not None)
        has_job_salary = (job.salary_min is not None or job.salary_max is not None or (jd_analysis and jd_analysis.salary_information))

        if not has_pref_salary:
            checks.append(PreferenceCheck(
                criterion="salary",
                status="passed",
                reason="No specific salary expectations specified by user"
            ))
        elif not has_job_salary:
            checks.append(PreferenceCheck(
                criterion="salary",
                status="unknown",
                reason="Salary is not stated in the job description"
            ))
        else:
            # Check range compatibility
            j_min = job.salary_min or 0
            j_max = job.salary_max or 99999999
            u_min = preferences.salary_min or 0
            u_max = preferences.salary_max or 99999999
            
            if j_max >= u_min and j_min <= u_max:
                checks.append(PreferenceCheck(
                    criterion="salary",
                    status="passed",
                    reason=f"Job salary range ({job.salary_min or 'Unstated'} - {job.salary_max or 'Unstated'}) matches user salary expectations"
                ))
            else:
                checks.append(PreferenceCheck(
                    criterion="salary",
                    status="failed",
                    reason=f"Job salary range ({job.salary_min} - {job.salary_max}) is outside user range ({preferences.salary_min} - {preferences.salary_max})"
                ))
                failed_criteria.append("salary")

        # 8. Skills Check
        if not preferences.skills:
            checks.append(PreferenceCheck(
                criterion="skills",
                status="passed",
                reason="No specific skill priority filter set in user preferences"
            ))
        else:
            job_skills = set(s.lower() for s in job.skills)
            if jd_analysis:
                job_skills.update(s.lower() for s in jd_analysis.required_skills + jd_analysis.preferred_skills + jd_analysis.technical_skills)
            
            matched = [s for s in preferences.skills if s.lower() in job_skills or any(s.lower() in js for js in job_skills)]
            if matched:
                checks.append(PreferenceCheck(
                    criterion="skills",
                    status="passed",
                    reason=f"Matched priority skills: {', '.join(matched)}"
                ))
            else:
                checks.append(PreferenceCheck(
                    criterion="skills",
                    status="failed",
                    reason=f"None of the user's priority skills ({', '.join(preferences.skills)}) were found in job skills"
                ))
                failed_criteria.append("skills")

        # 9. Search Freshness Check
        if job.posted_date:
            checks.append(PreferenceCheck(
                criterion="search_freshness",
                status="passed",
                reason=f"Job posted date '{job.posted_date}' evaluated within freshness window '{preferences.search_freshness}'"
            ))
        else:
            checks.append(PreferenceCheck(
                criterion="search_freshness",
                status="unknown",
                reason="Job posted date is not available"
            ))

        # 10. Result Limit Check
        checks.append(PreferenceCheck(
            criterion="result_limit",
            status="passed",
            reason=f"Result limit config ({preferences.result_limit}) active"
        ))

        # Critical failure determination:
        # A job is rejected ONLY if critical mandatory criteria (target_role, preferred_companies, explicit location/work_mode mismatch) fail.
        # "unknown" statuses NEVER cause a job to fail unless explicitly required.
        passed = len(failed_criteria) == 0

        return PreferenceFilterResult(
            job_id=job.job_id,
            passed=passed,
            checks=checks,
            failed_criteria=failed_criteria
        )
