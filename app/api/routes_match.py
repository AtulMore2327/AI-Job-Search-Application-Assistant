from fastapi import APIRouter, HTTPException
from typing import List
from app.models.matching import JobMatchResult, SkillGapAnalysis
from app.api.routes_jobs import _LATEST_PIPELINE_RESULTS

router = APIRouter(tags=["Matching"])

@router.get("/jobs/{job_id}/match", response_model=JobMatchResult)
def get_job_match(job_id: str):
    matches = _LATEST_PIPELINE_RESULTS.get("match_results", [])
    for match in matches:
        if match.job_id == job_id:
            return match
    raise HTTPException(status_code=404, detail="Match result not found for job_id")

@router.get("/jobs/{job_id}/skill-gap", response_model=SkillGapAnalysis)
def get_job_skill_gap(job_id: str):
    matches = _LATEST_PIPELINE_RESULTS.get("match_results", [])
    for match in matches:
        if match.job_id == job_id:
            return match.skill_gap
    raise HTTPException(status_code=404, detail="Skill gap analysis not found for job_id")
