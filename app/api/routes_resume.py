from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from typing import Optional
from pathlib import Path

from app.services.resume_analyzer import ResumeAnalyzer
from app.services.pdf_generator import PDFResumeGenerator
from app.models.candidate import CandidateProfile
from app.database.repositories import DatabaseRepository
from app.utils.text import clean_text
from app.config import settings

router = APIRouter(prefix="/resume", tags=["Resume"])
analyzer = ResumeAnalyzer()

_ACTIVE_CANDIDATE_PROFILE: Optional[CandidateProfile] = None

def get_active_candidate_profile() -> Optional[CandidateProfile]:
    global _ACTIVE_CANDIDATE_PROFILE
    return _ACTIVE_CANDIDATE_PROFILE

def set_active_candidate_profile(profile: CandidateProfile):
    global _ACTIVE_CANDIDATE_PROFILE
    _ACTIVE_CANDIDATE_PROFILE = profile
    try:
        DatabaseRepository.save_candidate_profile(profile)
    except Exception:
        pass

@router.post("/upload", response_model=CandidateProfile)
async def upload_resume(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename.lower()
        
        # Save raw uploaded PDF to disk if PDF
        if filename.endswith('.pdf'):
            text = analyzer.extract_text_from_pdf(content)
            try:
                (settings.DATA_DIR / "resume.pdf").write_bytes(content)
            except Exception:
                pass
        else:
            text = clean_text(content.decode('utf-8', errors='ignore'))
            
        if not text:
            text = "Candidate Profile: Data Analyst candidate with Python and SQL experience."
            
        profile = analyzer.analyze_resume(text)
        profile.raw_text = text
        set_active_candidate_profile(profile)
        
        # Generate PDF resume from extracted profile if not uploaded as pdf
        if not filename.endswith('.pdf'):
            try:
                PDFResumeGenerator.generate_pdf(profile, settings.DATA_DIR / "resume.pdf")
            except Exception:
                pass

        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume upload: {str(e)}")

@router.post("/analyze", response_model=CandidateProfile)
def analyze_resume_text(text: str = Form(...)):
    try:
        profile = analyzer.analyze_resume(text)
        profile.raw_text = text
        set_active_candidate_profile(profile)
        
        # Generate PDF resume from profile text
        try:
            PDFResumeGenerator.generate_pdf(profile, settings.DATA_DIR / "resume.pdf")
        except Exception:
            pass

        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download")
def download_resume():
    cand = get_active_candidate_profile() or CandidateProfile(name="Candidate")
    cand_name = (cand.name if cand and cand.name else "Candidate").replace(" [DEMO CANDIDATE]", "")
    
    pdf_path = settings.DATA_DIR / "resume.pdf"
    
    # Ensure PDF exists on disk
    if not pdf_path.exists() or not pdf_path.is_file():
        try:
            pdf_path = PDFResumeGenerator.generate_pdf(cand, pdf_path)
        except Exception as ex:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {ex}")

    clean_filename = f"Resume_{cand_name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_path.read_bytes(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={clean_filename}"}
    )

from pydantic import BaseModel

class CoverLetterPDFRequest(BaseModel):
    title: str
    company: str
    cover_letter: str

@router.post("/cover-letter/download-pdf")
def download_cover_letter_pdf(req: CoverLetterPDFRequest):
    cand = get_active_candidate_profile() or CandidateProfile(name="Candidate")
    cand_name = (cand.name if cand and cand.name else "Candidate").replace(" [DEMO CANDIDATE]", "")
    
    clean_comp = (req.company or "Company").replace("Company: ", "").split("|")[0].strip()
    pdf_filename = f"Cover_Letter_{cand_name.replace(' ', '_')}_{clean_comp.replace(' ', '_')}.pdf"
    output_path = settings.EXPORTS_DIR / pdf_filename
    
    try:
        gen_path = PDFResumeGenerator.generate_cover_letter_pdf(
            cand_name=cand_name,
            company=clean_comp,
            job_title=req.title,
            cover_text=req.cover_letter,
            output_path=output_path
        )
        return Response(
            content=gen_path.read_bytes(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to generate Cover Letter PDF: {ex}")

@router.get("/cover-letter/download-pdf")
def get_cover_letter_pdf(title: str = "Data Analyst", company: str = "Company", cover_letter: Optional[str] = None):
    cand = get_active_candidate_profile() or CandidateProfile(name="Candidate")
    cand_name = (cand.name if cand and cand.name else "Candidate").replace(" [DEMO CANDIDATE]", "")
    
    clean_comp = (company or "Company").replace("Company: ", "").split("|")[0].strip()
    pdf_filename = f"Cover_Letter_{cand_name.replace(' ', '_')}_{clean_comp.replace(' ', '_')}.pdf"
    output_path = settings.EXPORTS_DIR / pdf_filename
    
    cover_text = cover_letter or (
        f"Dear Hiring Team at {clean_comp},\n\n"
        f"I am writing to express my enthusiastic interest in the {title} position. "
        f"I hold strong skills in Python, SQL, Pandas, NumPy, alongside practical hands-on project experience in data cleaning, visualization, and analytical insights generation.\n\n"
        f"Attached is my resume for your review. I look forward to discussing how my analytical skills can add value to {clean_comp}.\n\n"
        f"Best regards,\n{cand_name}"
    )
    
    try:
        gen_path = PDFResumeGenerator.generate_cover_letter_pdf(
            cand_name=cand_name,
            company=clean_comp,
            job_title=title,
            cover_text=cover_text,
            output_path=output_path
        )
        return Response(
            content=gen_path.read_bytes(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to generate Cover Letter PDF: {ex}")


class CombinedPDFRequest(BaseModel):
    title: str
    company: str
    cover_letter: Optional[str] = ""

@router.post("/application/download-combined-pdf")
def download_combined_application_pdf(req: CombinedPDFRequest):
    cand = get_active_candidate_profile() or CandidateProfile(name="Candidate")
    cand_name = (cand.name if cand and cand.name else "Candidate").replace(" [DEMO CANDIDATE]", "")
    
    clean_comp = (req.company or "Company").replace("Company: ", "").split("|")[0].strip()
    pdf_filename = f"Application_Package_{cand_name.replace(' ', '_')}_{clean_comp.replace(' ', '_')}.pdf"
    output_path = settings.EXPORTS_DIR / pdf_filename
    
    try:
        gen_path = PDFResumeGenerator.generate_combined_application_pdf(
            profile=cand,
            company=clean_comp,
            job_title=req.title,
            cover_text=req.cover_letter or "",
            output_path=output_path
        )
        return Response(
            content=gen_path.read_bytes(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to generate Combined Application PDF: {ex}")

@router.get("/application/download-combined-pdf")
def get_combined_application_pdf(title: str = "Data Analyst", company: str = "Company", cover_letter: Optional[str] = None):
    cand = get_active_candidate_profile() or CandidateProfile(name="Candidate")
    cand_name = (cand.name if cand and cand.name else "Candidate").replace(" [DEMO CANDIDATE]", "")
    
    clean_comp = (company or "Company").replace("Company: ", "").split("|")[0].strip()
    pdf_filename = f"Application_Package_{cand_name.replace(' ', '_')}_{clean_comp.replace(' ', '_')}.pdf"
    output_path = settings.EXPORTS_DIR / pdf_filename
    
    cover_text = cover_letter or (
        f"Dear Hiring Team at {clean_comp},\n\n"
        f"I am writing to express my enthusiastic interest in the {title} position. "
        f"I hold strong skills in Python, SQL, Pandas, NumPy, alongside practical hands-on project experience in data cleaning, visualization, and analytical insights generation.\n\n"
        f"Attached is my resume for your review. I look forward to discussing how my analytical skills can add value to {clean_comp}.\n\n"
        f"Best regards,\n{cand_name}"
    )
    
    try:
        gen_path = PDFResumeGenerator.generate_combined_application_pdf(
            profile=cand,
            company=clean_comp,
            job_title=title,
            cover_text=cover_text,
            output_path=output_path
        )
        return Response(
            content=gen_path.read_bytes(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to generate Combined Application PDF: {ex}")


class HREmailPDFRequest(BaseModel):
    title: str
    company: str
    subject: Optional[str] = ""
    email_body: str

@router.post("/hr-email/download-pdf")
def download_hr_email_pdf(req: HREmailPDFRequest):
    cand = get_active_candidate_profile() or CandidateProfile(name="Candidate")
    cand_name = (cand.name if cand and cand.name else "Candidate").replace(" [DEMO CANDIDATE]", "")
    
    clean_comp = (req.company or "Company").replace("Company: ", "").split("|")[0].strip()
    pdf_filename = f"HR_Email_{cand_name.replace(' ', '_')}_{clean_comp.replace(' ', '_')}.pdf"
    output_path = settings.EXPORTS_DIR / pdf_filename
    
    try:
        gen_path = PDFResumeGenerator.generate_hr_email_pdf(
            cand_name=cand_name,
            company=clean_comp,
            job_title=req.title,
            email_subject=req.subject or f"Application for {req.title} Position - {cand_name}",
            email_body=req.email_body,
            output_path=output_path
        )
        return Response(
            content=gen_path.read_bytes(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to generate HR Email PDF: {ex}")

@router.get("/hr-email/download-pdf")
def get_hr_email_pdf(title: str = "Data Analyst", company: str = "Company", subject: Optional[str] = None, email_body: Optional[str] = None):
    cand = get_active_candidate_profile() or CandidateProfile(name="Candidate")
    cand_name = (cand.name if cand and cand.name else "Candidate").replace(" [DEMO CANDIDATE]", "")
    
    clean_comp = (company or "Company").replace("Company: ", "").split("|")[0].strip()
    pdf_filename = f"HR_Email_{cand_name.replace(' ', '_')}_{clean_comp.replace(' ', '_')}.pdf"
    output_path = settings.EXPORTS_DIR / pdf_filename
    
    clean_sub = subject or f"Application for {title} Role - {cand_name}"
    clean_body = email_body or (
        f"Dear Hiring Team at {clean_comp},\n\n"
        f"I am writing to express my enthusiastic interest in the {title} position. "
        f"I hold strong skills in Python, SQL, Pandas, NumPy, alongside practical hands-on project experience in data cleaning, visualization, and analytical insights generation.\n\n"
        f"Attached is my resume for your review. I look forward to discussing how my analytical skills can add value to {clean_comp}.\n\n"
        f"Best regards,\n{cand_name}"
    )
    
    try:
        gen_path = PDFResumeGenerator.generate_hr_email_pdf(
            cand_name=cand_name,
            company=clean_comp,
            job_title=title,
            email_subject=clean_sub,
            email_body=clean_body,
            output_path=output_path
        )
        return Response(
            content=gen_path.read_bytes(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to generate HR Email PDF: {ex}")








