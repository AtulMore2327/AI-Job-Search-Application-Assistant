"""
Resume-JD Matcher Service.
Performs deterministic, explainable resume-to-job matching, skill normalization,
required vs preferred skill separation, experience/education/location checks,
weighted scoring breakdown, and skill gap analysis integration.
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set

from app.models.candidate import CandidateProfile
from app.models.job import Job, JDAnalysis
from app.models.preferences import UserPreferences
from app.models.matching import MatchResult, SkillMatch, SkillGap
from app.services.skill_gap import SkillGapService
from app.utils.logging import get_logger

logger = get_logger("resume_matcher")

# Skill normalization mapping table for clean comparisons
SKILL_ALIASES: Dict[str, str] = {
    "python programming": "python",
    "python3": "python",
    "python 3": "python",
    "py": "python",
    "postgres": "postgresql",
    "postgresql database": "postgresql",
    "power-bi": "power bi",
    "powerbi": "power bi",
    "ms power bi": "power bi",
    "ms excel": "excel",
    "excel sheet": "excel",
    "excel spreadsheet": "excel",
    "microsoft excel": "excel",
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "node js": "node.js",
    "aws cloud": "aws",
    "amazon web services": "aws",
    "gcp": "google cloud",
    "google cloud platform": "google cloud",
    "scikit learn": "scikit-learn",
    "scikitlearn": "scikit-learn",
    "sklearn": "scikit-learn",
    "k8s": "kubernetes",
    "docker container": "docker",
    "ts": "typescript",
    "js": "javascript",
}


def normalize_skill(skill: str) -> str:
    """
    Normalize skill string for exact comparison without altering display names.
    
    Args:
        skill: Raw skill string.
        
    Returns:
        Clean normalized skill token.
    """
    if not skill:
        return ""
    clean = skill.lower().strip()
    clean = re.sub(r'[^\w\s\-\.\+#]', '', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return SKILL_ALIASES.get(clean, clean)


class ResumeMatcherService:
    """Service for deterministic explainable matching of candidate profiles against job postings."""

    def __init__(self, skill_gap_service: Optional[SkillGapService] = None):
        self.skill_gap_service = skill_gap_service or SkillGapService()

    def match_candidate_to_job(
        self,
        candidate: CandidateProfile,
        job: Job,
        jd_analysis: Optional[JDAnalysis] = None,
        preferences: Optional[UserPreferences] = None,
        use_cache: bool = True
    ) -> MatchResult:
        """
        Perform complete deterministic match between CandidateProfile and Job / JDAnalysis.
        
        Args:
            candidate: CandidateProfile instance.
            job: Job model instance.
            jd_analysis: Optional JDAnalysis model.
            preferences: Optional UserPreferences model.
            use_cache: Whether to use SQLite match cache repository.
            
        Returns:
            Validated MatchResult with deterministic score breakdown and explanations.
        """
        if use_cache:
            try:
                from app.database.repositories import MatchCacheRepository
                cached = MatchCacheRepository().get_match_result(candidate, job.job_id, jd_analysis=jd_analysis)
                if cached:
                    return cached
            except Exception as ce:
                logger.debug(f"Match cache check skipped/failed: {ce}")
        # Gather all candidate evidence text & skills
        candidate_skill_tokens: Dict[str, str] = {}  # normalized -> original
        
        for sk in candidate.skills + candidate.tools + candidate.certifications + candidate.keywords:
            norm = normalize_skill(sk)
            if norm:
                candidate_skill_tokens[norm] = sk

        # Also extract skills from experience tech stacks
        for exp in candidate.experience:
            for tech in exp.technologies:
                norm = normalize_skill(tech)
                if norm:
                    candidate_skill_tokens[norm] = tech

        # Also check raw text for keyword presence
        raw_text_lower = (candidate.raw_text or "").lower()

        # JD skills
        jd_required = jd_analysis.required_skills if jd_analysis else job.skills
        jd_preferred = jd_analysis.preferred_skills if jd_analysis else []
        jd_tech = jd_analysis.technical_skills if jd_analysis else []

        # Combine technical skills into required if required is empty
        if not jd_required and jd_tech:
            jd_required = jd_tech

        # Match required skills
        matched_req: List[str] = []
        missing_req: List[str] = []
        partial_matches: List[Dict[str, str]] = []

        for req in jd_required:
            req_norm = normalize_skill(req)
            if not req_norm:
                continue
                
            if req_norm in candidate_skill_tokens:
                matched_req.append(req)
            elif req_norm in raw_text_lower:
                matched_req.append(req)
            else:
                # Check for partial matches (broad skill vs specific library)
                partial_found = False
                for c_norm, c_orig in candidate_skill_tokens.items():
                    if c_norm and (c_norm in req_norm or req_norm in c_norm):
                        partial_matches.append({
                            "skill": req,
                            "status": "partial",
                            "evidence": c_orig
                        })
                        partial_found = True
                        break
                if not partial_found:
                    missing_req.append(req)

        # Match preferred skills
        matched_pref: List[str] = []
        missing_pref: List[str] = []

        for pref in jd_preferred:
            pref_norm = normalize_skill(pref)
            if not pref_norm:
                continue
                
            if pref_norm in candidate_skill_tokens or pref_norm in raw_text_lower:
                matched_pref.append(pref)
            else:
                partial_found = False
                for c_norm, c_orig in candidate_skill_tokens.items():
                    if c_norm and (c_norm in pref_norm or pref_norm in c_norm):
                        partial_matches.append({
                            "skill": pref,
                            "status": "partial",
                            "evidence": c_orig
                        })
                        partial_found = True
                        break
                if not partial_found:
                    missing_pref.append(pref)

        # 2. Evaluate Experience Match
        exp_eval = self._evaluate_experience(candidate, job, jd_analysis)

        # 3. Evaluate Education Match
        edu_eval = self._evaluate_education(candidate, jd_analysis)

        # 4. Evaluate Location Match
        loc_eval = self._evaluate_location(preferences, job, jd_analysis)

        # 5. Evaluate Work Mode Match
        wm_eval = self._evaluate_work_mode(preferences, job, jd_analysis)

        # 6. Evaluate Employment Type Match
        et_eval = self._evaluate_employment_type(preferences, job, jd_analysis)

        # 7. Evaluate Other Fit / Keywords
        other_eval = self._evaluate_other_fit(candidate, job, jd_analysis)

        # 8. Calculate Deterministic Match Score & Breakdown
        score_breakdown, match_score = self._calculate_score(
            matched_req=matched_req,
            missing_req=missing_req,
            matched_pref=matched_pref,
            missing_pref=missing_pref,
            partial_matches=partial_matches,
            exp_eval=exp_eval,
            edu_eval=edu_eval,
            loc_eval=loc_eval,
            wm_eval=wm_eval,
            et_eval=et_eval,
            other_score=other_eval
        )

        # 9. Skill Gap Analysis
        dummy_jd = jd_analysis or JDAnalysis(
            job_id=job.job_id,
            title=job.title,
            company=job.company,
            required_skills=jd_required,
            preferred_skills=jd_preferred
        )
        gap_analysis = self.skill_gap_service.analyze_gap(
            candidate=candidate,
            jd_analysis=dummy_jd,
            matched_required=matched_req,
            missing_required=missing_req,
            matched_preferred=matched_pref,
            missing_preferred=missing_pref,
            partial_matches=partial_matches
        )

        # 10. Generate Strengths, Concerns, and Summary Explanation
        strengths, concerns, explanation = self._generate_explanations(
            match_score=match_score,
            matched_req=matched_req,
            missing_req=missing_req,
            matched_pref=matched_pref,
            missing_pref=missing_pref,
            exp_eval=exp_eval,
            edu_eval=edu_eval,
            loc_eval=loc_eval,
            job=job
        )

        result = MatchResult(
            job_id=job.job_id,
            candidate_name=candidate.name or "Candidate",
            match_score=match_score,
            score_breakdown=score_breakdown,
            matched_required_skills=matched_req,
            missing_required_skills=missing_req,
            matched_preferred_skills=matched_pref,
            missing_preferred_skills=missing_pref,
            partial_matches=partial_matches,
            experience_match=exp_eval,
            education_match=edu_eval,
            location_match=loc_eval,
            work_mode_match=wm_eval,
            employment_type_match=et_eval,
            strengths=strengths,
            concerns=concerns,
            skill_gap=gap_analysis,
            explanation=explanation
        )

        if use_cache:
            try:
                from app.database.repositories import MatchCacheRepository
                MatchCacheRepository().save_match_result(candidate, job.job_id, result, jd_analysis=jd_analysis)
            except Exception as se:
                logger.debug(f"Failed to save MatchResult to cache: {se}")

        return result

    def _evaluate_experience(
        self,
        candidate: CandidateProfile,
        job: Job,
        jd_analysis: Optional[JDAnalysis]
    ) -> Dict[str, Any]:
        """Evaluate candidate experience level against JD requirements."""
        req_str = (jd_analysis.experience_requirements if jd_analysis else "") or job.experience_level or ""
        req_str_clean = req_str.lower().strip()

        if not req_str_clean:
            return {
                "status": "unknown",
                "candidate_experience": f"{len(candidate.experience)} role(s) listed",
                "jd_required": "Unstated",
                "reason": "Experience requirement is not explicitly stated in the job description"
            }

        # Check for fresher / entry level
        is_fresher_req = any(term in req_str_clean for term in ["fresher", "entry", "0 year", "0-1", "0-2"])
        cand_has_exp = len(candidate.experience) > 0

        if is_fresher_req:
            return {
                "status": "passed",
                "candidate_experience": f"{len(candidate.experience)} work/internship experience(s)",
                "jd_required": req_str,
                "reason": f"Role accepts freshers / entry level and candidate profile fits ({req_str})"
            }

        # Estimate candidate years
        cand_years = 0.0
        if cand_has_exp:
            cand_years = float(len(candidate.experience))  # Simple benchmark count

        # Extract required minimum years using regex
        match = re.search(r'(\d+)\s*\+?\s*(?:-\s*(\d+))?\s*year', req_str_clean)
        if match:
            min_req = float(match.group(1))
            if cand_years >= min_req:
                return {
                    "status": "passed",
                    "candidate_experience": f"Approx {cand_years} year(s) from {len(candidate.experience)} role(s)",
                    "jd_required": req_str,
                    "reason": f"Candidate experience meets or exceeds required {min_req} year(s)"
                }
            else:
                return {
                    "status": "failed",
                    "candidate_experience": f"Approx {cand_years} year(s) from {len(candidate.experience)} role(s)",
                    "jd_required": req_str,
                    "reason": f"Job requires {min_req}+ year(s) experience; candidate has approx {cand_years} year(s)"
                }

        return {
            "status": "passed",
            "candidate_experience": f"{len(candidate.experience)} listed role(s)",
            "jd_required": req_str,
            "reason": f"Experience requirements evaluated: {req_str}"
        }

    def _evaluate_education(
        self,
        candidate: CandidateProfile,
        jd_analysis: Optional[JDAnalysis]
    ) -> Dict[str, Any]:
        """Evaluate candidate degree level against JD requirements."""
        req_str = (jd_analysis.education_requirements if jd_analysis else "") or ""
        req_str_clean = req_str.lower().strip()

        cand_degrees = [e.degree.lower() for e in candidate.education if e.degree]

        if not req_str_clean:
            return {
                "status": "unknown",
                "candidate_education": ", ".join([e.degree for e in candidate.education]) if candidate.education else "Unstated",
                "jd_required": "Unstated",
                "reason": "Education requirements are not stated in the job description"
            }

        if not candidate.education:
            return {
                "status": "unknown",
                "candidate_education": "None listed",
                "jd_required": req_str,
                "reason": "No education section found in candidate profile"
            }

        has_bachelors = any(d in deg for deg in cand_degrees for d in ["b.tech", "b.e", "b.sc", "bachelor", "bs", "degree"])
        has_masters = any(d in deg for deg in cand_degrees for d in ["m.tech", "m.e", "m.sc", "master", "ms", "mba", "phd"])

        has_masters_req = any(m in req_str_clean for m in ["master", "m.tech", "m.sc", "mba", "phd", "doctorate"])
        has_bachelors_req = any(b in req_str_clean for b in ["bachelor", "b.tech", "b.e", "b.sc", "bs", "degree"])

        if has_masters_req:
            if has_masters:
                return {
                    "status": "passed",
                    "candidate_education": candidate.education[0].degree,
                    "jd_required": req_str,
                    "reason": f"Candidate possesses required Master's/Advanced degree ({candidate.education[0].degree})"
                }
            else:
                return {
                    "status": "failed",
                    "candidate_education": candidate.education[0].degree if candidate.education else "None",
                    "jd_required": req_str,
                    "reason": f"Job requires Master's/Advanced degree ({req_str}); candidate has Bachelor's/Other"
                }

        if has_bachelors_req:
            if has_bachelors or has_masters:
                return {
                    "status": "passed",
                    "candidate_education": candidate.education[0].degree,
                    "jd_required": req_str,
                    "reason": f"Candidate possesses required degree ({candidate.education[0].degree})"
                }
            else:
                return {
                    "status": "failed",
                    "candidate_education": candidate.education[0].degree if candidate.education else "None",
                    "jd_required": req_str,
                    "reason": f"Job requires Bachelor's degree ({req_str}); candidate has insufficient degree level"
                }

        return {
            "status": "passed",
            "candidate_education": candidate.education[0].degree if candidate.education else "Unstated",
            "jd_required": req_str,
            "reason": f"Education matched: {req_str}"
        }

    def _evaluate_location(
        self,
        preferences: Optional[UserPreferences],
        job: Job,
        jd_analysis: Optional[JDAnalysis]
    ) -> Dict[str, Any]:
        pref_loc = preferences.location.lower().strip() if preferences else "any"
        job_loc = (job.location or "Unknown").lower().strip()

        if pref_loc in ["any", "", "all"]:
            return {"status": "passed", "reason": "Candidate/user accepts any location"}

        if job_loc == "unknown":
            return {"status": "unknown", "reason": "Job location is not specified"}

        if pref_loc in job_loc or job_loc in pref_loc or job.work_mode.lower() == "remote":
            return {"status": "passed", "reason": f"Location '{job.location}' matches preference '{preferences.location}'"}

        return {"status": "failed", "reason": f"Location '{job.location}' differs from preferred '{preferences.location}'"}

    def _evaluate_work_mode(
        self,
        preferences: Optional[UserPreferences],
        job: Job,
        jd_analysis: Optional[JDAnalysis]
    ) -> Dict[str, Any]:
        pref_wm = preferences.work_mode.lower().strip() if preferences else "any"
        job_wm = job.work_mode.lower().strip() if job.work_mode else "unknown"

        if pref_wm in ["any", "", "all"]:
            return {"status": "passed", "reason": "User accepts any work mode"}

        if job_wm == "unknown":
            return {"status": "unknown", "reason": "Work mode is not stated"}

        if pref_wm in job_wm or job_wm in pref_wm:
            return {"status": "passed", "reason": f"Work mode '{job.work_mode}' matches preference '{preferences.work_mode}'"}

        return {"status": "failed", "reason": f"Work mode '{job.work_mode}' does not match preference '{preferences.work_mode}'"}

    def _evaluate_employment_type(
        self,
        preferences: Optional[UserPreferences],
        job: Job,
        jd_analysis: Optional[JDAnalysis]
    ) -> Dict[str, Any]:
        pref_et = preferences.employment_type.lower().strip() if preferences else "any"
        job_et = job.employment_type.lower().strip() if job.employment_type else "unknown"

        if pref_et in ["any", "", "all"]:
            return {"status": "passed", "reason": "User accepts any employment type"}

        if job_et == "unknown":
            return {"status": "unknown", "reason": "Employment type is not stated"}

        if pref_et in job_et or job_et in pref_et:
            return {"status": "passed", "reason": f"Employment type '{job.employment_type}' matches preference '{preferences.employment_type}'"}

        return {"status": "failed", "reason": f"Employment type '{job.employment_type}' does not match preference '{preferences.employment_type}'"}

    def _evaluate_other_fit(
        self,
        candidate: CandidateProfile,
        job: Job,
        jd_analysis: Optional[JDAnalysis]
    ) -> float:
        """Calculate score for keyword and summary overlap (0.0 to 5.0)."""
        jd_text = (jd_analysis.summary + " " + jd_analysis.raw_jd_text) if jd_analysis and jd_analysis.raw_jd_text else job.description_snippet
        jd_text_lower = jd_text.lower()
        
        cand_keywords = [k.lower() for k in candidate.keywords + candidate.skills if k]
        if not cand_keywords:
            return 2.5

        matched_count = sum(1 for k in cand_keywords if k in jd_text_lower)
        ratio = matched_count / float(len(cand_keywords))
        return min(5.0, round(ratio * 5.0, 2))

    def _calculate_score(
        self,
        matched_req: List[str],
        missing_req: List[str],
        matched_pref: List[str],
        missing_pref: List[str],
        partial_matches: List[Dict[str, str]],
        exp_eval: Dict[str, Any],
        edu_eval: Dict[str, Any],
        loc_eval: Dict[str, Any],
        wm_eval: Dict[str, Any],
        et_eval: Dict[str, Any],
        other_score: float
    ) -> Tuple[Dict[str, float], float]:
        """
        Calculate deterministic weighted match score (0-100).
        
        Weights:
          - Required Skills:  40% (40.0 pts)
          - Preferred Skills: 15% (15.0 pts)
          - Experience:       15% (15.0 pts)
          - Education:        10% (10.0 pts)
          - Location:          5% ( 5.0 pts)
          - Work Mode:         5% ( 5.0 pts)
          - Employment Type:   5% ( 5.0 pts)
          - Other Fit:         5% ( 5.0 pts)
        """
        # 1. Required Skills (40 pts)
        total_req = len(matched_req) + len(missing_req)
        if total_req > 0:
            req_score = (len(matched_req) / float(total_req)) * 40.0
            # Add partial match credit
            partial_req = [p for p in partial_matches if p.get("skill") in missing_req]
            req_score += (len(partial_req) * 0.5 / float(total_req)) * 40.0
            req_score = min(40.0, req_score)
        else:
            req_score = 30.0  # Default neutral credit when JD lists no explicit required skills

        # 2. Preferred Skills (15 pts)
        total_pref = len(matched_pref) + len(missing_pref)
        if total_pref > 0:
            pref_score = (len(matched_pref) / float(total_pref)) * 15.0
            pref_score = min(15.0, pref_score)
        else:
            pref_score = 10.0  # Default neutral credit when JD lists no preferred skills

        # 3. Experience (15 pts)
        if exp_eval["status"] == "passed":
            exp_score = 15.0
        elif exp_eval["status"] == "unknown":
            exp_score = 10.0
        else:
            exp_score = 0.0

        # 4. Education (10 pts)
        if edu_eval["status"] == "passed":
            edu_score = 10.0
        elif edu_eval["status"] == "unknown":
            edu_score = 7.0
        else:
            edu_score = 0.0

        # 5. Location (5 pts)
        if loc_eval["status"] == "passed":
            loc_score = 5.0
        elif loc_eval["status"] == "unknown":
            loc_score = 3.5
        else:
            loc_score = 0.0

        # 6. Work Mode (5 pts)
        if wm_eval["status"] == "passed":
            wm_score = 5.0
        elif wm_eval["status"] == "unknown":
            wm_score = 3.5
        else:
            wm_score = 0.0

        # 7. Employment Type (5 pts)
        if et_eval["status"] == "passed":
            et_score = 5.0
        elif et_eval["status"] == "unknown":
            et_score = 3.5
        else:
            et_score = 0.0

        # 8. Other Fit (5 pts)
        oth_score = min(5.0, max(0.0, other_score))

        breakdown = {
            "required_skills": round(req_score, 2),
            "preferred_skills": round(pref_score, 2),
            "experience": round(exp_score, 2),
            "education": round(edu_score, 2),
            "location": round(loc_score, 2),
            "work_mode": round(wm_score, 2),
            "employment_type": round(et_score, 2),
            "other": round(oth_score, 2),
        }

        total_score = round(sum(breakdown.values()), 2)
        total_score = max(0.0, min(100.0, total_score))
        breakdown["total"] = total_score

        return breakdown, total_score

    def _generate_explanations(
        self,
        match_score: float,
        matched_req: List[str],
        missing_req: List[str],
        matched_pref: List[str],
        missing_pref: List[str],
        exp_eval: Dict[str, Any],
        edu_eval: Dict[str, Any],
        loc_eval: Dict[str, Any],
        job: Job
    ) -> Tuple[List[str], List[str], str]:
        """Generate human-readable strengths, concerns, and overall summary explanation."""
        strengths: List[str] = []
        concerns: List[str] = []

        if matched_req:
            strengths.append(f"Matched required skill(s): {', '.join(matched_req)}")
        if matched_pref:
            strengths.append(f"Matched preferred skill(s): {', '.join(matched_pref)}")
        if exp_eval["status"] == "passed":
            strengths.append(f"Experience alignment: {exp_eval['reason']}")
        if edu_eval["status"] == "passed":
            strengths.append(f"Education alignment: {edu_eval['reason']}")

        if missing_req:
            concerns.append(f"Missing required skill(s): {', '.join(missing_req)}")
        if missing_pref:
            concerns.append(f"Missing preferred skill(s): {', '.join(missing_pref)}")
        if exp_eval["status"] == "failed":
            concerns.append(f"Experience gap: {exp_eval['reason']}")
        if edu_eval["status"] == "failed":
            concerns.append(f"Education gap: {edu_eval['reason']}")

        explanation = (
            f"Overall Match Score: {match_score:.1f}/100 for position '{job.title}' at {job.company}. "
            f"Candidate matches {len(matched_req)}/{len(matched_req)+len(missing_req)} required skills and "
            f"{len(matched_pref)}/{len(matched_pref)+len(missing_pref)} preferred skills. "
            f"Experience check: {exp_eval['status'].upper()} ({exp_eval['reason']}). "
            f"Education check: {edu_eval['status'].upper()} ({edu_eval['reason']})."
        )

        return strengths, concerns, explanation
