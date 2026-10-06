from typing import List
from app.models.candidate import CandidateProfile
from app.models.job import JobPosting
from app.models.matching import SkillGapAnalysis
from rapidfuzz import fuzz

class SkillGapAnalyzer:
    @staticmethod
    def analyze_skill_gap(candidate: CandidateProfile, job: JobPosting) -> SkillGapAnalysis:
        """
        Categorize job skills against candidate's profile into matched, partially matched, and missing categories.
        """
        cand_skills = [s.lower() for s in (candidate.skills + candidate.tools + candidate.keywords)]
        req_skills = job.required_skills or ["Python", "SQL"]
        pref_skills = job.preferred_skills or []

        matched = []
        partially_matched = []
        missing_must_have = []
        missing_nice_to_have = []

        # Check required skills
        for r_skill in req_skills:
            r_lower = r_skill.lower()
            exact_found = any(r_lower == c_s for c_s in cand_skills)
            if exact_found:
                matched.append(r_skill)
            else:
                fuzzy_found = any(
                    (len(r_lower) >= 4 and fuzz.partial_ratio(r_lower, c_s) >= 85)
                    for c_s in cand_skills
                )
                if fuzzy_found:
                    partially_matched.append(r_skill)
                else:
                    missing_must_have.append(r_skill)

        # Check preferred skills
        for p_skill in pref_skills:
            p_lower = p_skill.lower()
            if any(p_lower == c_s for c_s in cand_skills):
                if p_skill not in matched:
                    matched.append(p_skill)
            elif any(len(p_lower) >= 4 and fuzz.partial_ratio(p_lower, c_s) >= 85 for c_s in cand_skills):
                if p_skill not in partially_matched:
                    partially_matched.append(p_skill)
            else:
                if p_skill not in missing_nice_to_have:
                    missing_nice_to_have.append(p_skill)

        return SkillGapAnalysis(
            matched_skills=matched,
            partially_matched_skills=partially_matched,
            missing_must_have=missing_must_have,
            missing_nice_to_have=missing_nice_to_have,
            not_evidenced=[]
        )

SkillGapService = SkillGapAnalyzer
