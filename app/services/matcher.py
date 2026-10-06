from typing import List, Tuple
from rapidfuzz import fuzz

from app.models.candidate import CandidateProfile
from app.models.job import JobPosting, JobSearchPreferences
from app.models.matching import JobMatchResult, MatchScoreBreakdown
from app.services.skill_gap import SkillGapAnalyzer

class ResumeJDMatcher:
    # Deterministic Configurable Weights (Sum = 100%)
    WEIGHT_SKILLS = 45.0
    WEIGHT_EXPERIENCE = 20.0
    WEIGHT_EDUCATION = 10.0
    WEIGHT_RESPONSIBILITIES = 15.0
    WEIGHT_KEYWORDS = 10.0

    @classmethod
    def filter_and_match_job(
        cls,
        candidate: CandidateProfile,
        job: JobPosting,
        prefs: JobSearchPreferences
    ) -> JobMatchResult:
        """
        1. Check preference filtering rules (Location, Experience, Work Mode, Role).
        2. Calculate weighted deterministic match score (0-100%).
        3. Perform Skill Gap analysis.
        """
        pref_matched, reasons = cls._check_preference_filtering(job, prefs)
        
        # Skill Gap Analysis
        skill_gap = SkillGapAnalyzer.analyze_skill_gap(candidate, job)

        # 1. Skills Score (Max 45)
        total_req = len(job.required_skills) or 1
        matched_cnt = len(skill_gap.matched_skills)
        partial_cnt = len(skill_gap.partially_matched_skills)
        skills_pct = min(1.0, (matched_cnt + (partial_cnt * 0.5)) / total_req)
        score_skills = round(skills_pct * cls.WEIGHT_SKILLS, 1)

        # 2. Experience Score (Max 20)
        # Check if candidate has experience or is fresher aligned with job requirement
        score_exp = cls._calculate_experience_score(candidate, job, prefs)

        # 3. Education Score (Max 10)
        score_edu = cls._calculate_education_score(candidate, job)

        # 4. Responsibilities / Projects Score (Max 15)
        score_resp = cls._calculate_responsibilities_score(candidate, job)

        # 5. Keywords Score (Max 10)
        score_kw = cls._calculate_keywords_score(candidate, job)

        # Total Deterministic Match Score
        total_score = round(score_skills + score_exp + score_edu + score_resp + score_kw, 1)
        total_score = min(100.0, max(0.0, total_score))

        breakdown = MatchScoreBreakdown(
            skills_score=score_skills,
            experience_score=score_exp,
            education_score=score_edu,
            responsibilities_score=score_resp,
            keywords_score=score_kw
        )

        explanation = (
            f"Match score {total_score}% calculated deterministically: "
            f"Skills ({score_skills}/45), Experience ({score_exp}/20), Education ({score_edu}/10), "
            f"Projects/Responsibilities ({score_resp}/15), Keywords ({score_kw}/10)."
        )

        return JobMatchResult(
            job_id=job.job_id,
            job_title=job.title,
            company=job.company,
            match_score=total_score,
            breakdown=breakdown,
            skill_gap=skill_gap,
            explanation=explanation,
            is_preference_match=pref_matched,
            preference_reasons=reasons
        )

    @classmethod
    def _check_preference_filtering(cls, job: JobPosting, prefs: JobSearchPreferences) -> Tuple[bool, List[str]]:
        reasons = []
        is_match = True

        # Location Check
        if prefs.location and prefs.location.lower() not in job.location.lower() and "remote" not in job.work_mode.lower():
            reasons.append(f"Location mismatch: Job is in '{job.location}', preferred '{prefs.location}'")

        # Work Mode Check
        if prefs.work_mode and prefs.work_mode != "Any" and prefs.work_mode.lower() not in job.work_mode.lower():
            reasons.append(f"Work mode mismatch: Job is '{job.work_mode}', preferred '{prefs.work_mode}'")

        # Role similarity check
        role_sim = fuzz.token_set_ratio(prefs.target_role.lower(), job.title.lower())
        if role_sim < 40:
            reasons.append(f"Role mismatch: Job title '{job.title}' differs significantly from target '{prefs.target_role}'")
            is_match = False

        return is_match, reasons

    @classmethod
    def _calculate_experience_score(cls, candidate: CandidateProfile, job: JobPosting, prefs: JobSearchPreferences) -> float:
        # If fresher preferred and candidate has entry level/trainee or <1 year exp
        cand_exp_count = len(candidate.experience)
        if prefs.experience_level.lower() in ["fresher", "entry", "0-1"]:
            return cls.WEIGHT_EXPERIENCE
        if cand_exp_count >= 1:
            return cls.WEIGHT_EXPERIENCE
        return round(cls.WEIGHT_EXPERIENCE * 0.75, 1)

    @classmethod
    def _calculate_education_score(cls, candidate: CandidateProfile, job: JobPosting) -> float:
        if candidate.education:
            deg = candidate.education[0].degree.lower()
            if any(k in deg for k in ["b.sc", "b.tech", "b.e", "b.ca", "bachelor", "master", "m.sc"]):
                return cls.WEIGHT_EDUCATION
        return round(cls.WEIGHT_EDUCATION * 0.5, 1)

    @classmethod
    def _calculate_responsibilities_score(cls, candidate: CandidateProfile, job: JobPosting) -> float:
        if candidate.projects or candidate.experience:
            return cls.WEIGHT_RESPONSIBILITIES
        return round(cls.WEIGHT_RESPONSIBILITIES * 0.5, 1)

    @classmethod
    def _calculate_keywords_score(cls, candidate: CandidateProfile, job: JobPosting) -> float:
        job_kw = set(job.title.lower().split() + [s.lower() for s in job.required_skills])
        cand_kw = set([k.lower() for k in candidate.keywords] + [s.lower() for s in candidate.skills])
        overlap = job_kw.intersection(cand_kw)
        if not job_kw:
            return cls.WEIGHT_KEYWORDS
        ratio = len(overlap) / len(job_kw)
        return round(min(cls.WEIGHT_KEYWORDS, ratio * cls.WEIGHT_KEYWORDS), 1)
