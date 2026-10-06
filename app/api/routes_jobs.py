from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.models.job import JobSearchPreferences, JobPosting
from app.services.orchestrator import orchestrator
from app.api.routes_resume import get_active_candidate_profile

router = APIRouter(tags=["Jobs & Pipeline"])

_LATEST_PIPELINE_RESULTS: Dict[str, Any] = {}

@router.post("/search/jobs")
def run_job_search_pipeline(prefs: JobSearchPreferences):
    global _LATEST_PIPELINE_RESULTS
    try:
        active_profile = get_active_candidate_profile()
        if active_profile:
            input_data = active_profile
        else:
            input_data = "Data Analyst candidate with skills in Python, SQL, Power BI, Excel."
            
        results = orchestrator.run_pipeline(input_data, prefs, is_pdf=False)
        _LATEST_PIPELINE_RESULTS = results
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs", response_model=List[JobPosting])
def get_jobs():
    return _LATEST_PIPELINE_RESULTS.get("jobs", [])

@router.get("/jobs/{job_id}", response_model=JobPosting)
def get_job_by_id(job_id: str):
    jobs = _LATEST_PIPELINE_RESULTS.get("jobs", [])
    for job in jobs:
        if job.job_id == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")

class DirectEmailRequest(BaseModel):
    job_id: str
    to_email: str
    subject: Optional[str] = None
    body: Optional[str] = None

class SMTPConfigRequest(BaseModel):
    sender_email: str
    sender_password: str

@router.post("/config/smtp")
def update_smtp_config(req: SMTPConfigRequest):
    from app.config import settings
    import os
    settings.SMTP_SENDER_EMAIL = req.sender_email.strip()
    settings.SMTP_SENDER_PASSWORD = req.sender_password.strip()
    os.environ["SMTP_SENDER_EMAIL"] = req.sender_email.strip()
    os.environ["SMTP_SENDER_PASSWORD"] = req.sender_password.strip()
    
    # Optionally append/update in .env file
    env_path = settings.BASE_DIR / ".env"
    try:
        content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
        if "SMTP_SENDER_EMAIL=" in content:
            lines = content.splitlines()
            new_lines = []
            for line in lines:
                if line.startswith("SMTP_SENDER_EMAIL="):
                    new_lines.append(f"SMTP_SENDER_EMAIL={req.sender_email.strip()}")
                elif line.startswith("SMTP_SENDER_PASSWORD="):
                    new_lines.append(f"SMTP_SENDER_PASSWORD={req.sender_password.strip()}")
                else:
                    new_lines.append(line)
            env_path.write_text("\n".join(new_lines), encoding="utf-8")
        else:
            with open(env_path, "a", encoding="utf-8") as f:
                f.write(f"\nSMTP_SENDER_EMAIL={req.sender_email.strip()}\nSMTP_SENDER_PASSWORD={req.sender_password.strip()}\n")
    except Exception as ex:
        pass

    return {
        "success": True,
        "message": f"✅ Direct Email Sender ({req.sender_email.strip()}) configured successfully! All applications will now send directly to HR with Resume PDF & Cover Letter attached."
    }

@router.post("/jobs/send-email")
def send_direct_hr_email(req: DirectEmailRequest):
    global _LATEST_PIPELINE_RESULTS
    jobs = _LATEST_PIPELINE_RESULTS.get("jobs", [])
    target_job = None
    for j in jobs:
        if j.job_id == req.job_id:
            target_job = j
            break
            
    if not target_job:
        target_job = JobPosting(
            job_id=req.job_id,
            title="Data Analyst",
            company="Tech Company",
            location="India",
            hr_email=req.to_email
        )
        
    profile = _LATEST_PIPELINE_RESULTS.get("candidate_profile") or get_active_candidate_profile()
    
    from app.services.email_dispatcher import EmailDispatcherService
    res = EmailDispatcherService.send_application_email(
        to_email=req.to_email,
        subject=req.subject or f"Application for {target_job.title} - Candidate",
        body=req.body or "",
        job=target_job,
        profile=profile
    )
    return res


