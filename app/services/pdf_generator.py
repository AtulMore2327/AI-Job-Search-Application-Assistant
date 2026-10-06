"""
PDF Resume Generator Service using FPDF2.
Generates clean, professional PDF resumes for candidate job applications.
"""

from pathlib import Path
from fpdf import FPDF
from app.models.candidate import CandidateProfile
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("pdf_generator")

def sanitize_pdf_text(text: str) -> str:
    """Replaces non-latin characters with standard ASCII equivalents for Helvetica font."""
    if not text:
        return ""
    replacements = {
        "•": "-",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "\u2022": "-",
        "\u2013": "-",
        "\u2014": "-"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")

class PDFResumeGenerator:
    """Generates styled PDF Resume documents for candidate applications."""

    @classmethod
    def generate_pdf(cls, profile: CandidateProfile, output_path: Path) -> Path:
        """
        Builds a modern, professional PDF resume file.
        """
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            cand_name = sanitize_pdf_text((profile.name or "Candidate").replace(" [DEMO CANDIDATE]", ""))
            cand_email = sanitize_pdf_text(profile.email or "candidate@example.com")
            cand_phone = sanitize_pdf_text(profile.phone or "+91-9876543210")
            cand_loc = sanitize_pdf_text(profile.location or "India")
            
            # Header Name Banner
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(16, 24, 40) # Dark navy
            pdf.cell(0, 10, cand_name, ln=True, align="L")
            
            # Contact Info
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(71, 85, 105)
            contact_str = f"Email: {cand_email} | Phone: {cand_phone} | Location: {cand_loc}"
            pdf.cell(0, 6, contact_str, ln=True, align="L")
            pdf.ln(3)
            
            # Horizontal Line Divider
            pdf.set_draw_color(99, 102, 241) # Indigo accent
            pdf.set_line_width(0.8)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            # Section: Executive Professional Summary
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(16, 185, 129) # Emerald Green header
            pdf.cell(0, 7, "PROFESSIONAL SUMMARY", ln=True)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(30, 41, 59)
            summary_text = sanitize_pdf_text(profile.summary or (
                "Results-driven Data Analyst with practical expertise in Python, SQL database querying, "
                "Power BI interactive dashboard design, Pandas/NumPy data transformations, and business insights generation. "
                "Experienced in executing data cleaning workflows and communicating analytical findings to stakeholders."
            ))
            pdf.multi_cell(0, 5, summary_text)
            pdf.ln(4)

            # Section: Key Technical Skills
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(16, 185, 129)
            pdf.cell(0, 7, "CORE TECHNICAL SKILLS", ln=True)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(30, 41, 59)
            
            skills_list = profile.skills if profile and profile.skills else [
                "Python", "SQL", "Pandas", "NumPy", "Power BI", "Excel",
                "Data Cleaning & Preprocessing", "Exploratory Data Analysis (EDA)",
                "Analytical Insights Generation"
            ]
            skills_text = sanitize_pdf_text(" | ".join(skills_list))
            pdf.multi_cell(0, 5, skills_text)
            pdf.ln(4)

            # Section: Relevant Projects & Experience
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(16, 185, 129)
            pdf.cell(0, 7, "PROJECTS & ANALYTICAL WORK", ln=True)
            
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 6, "1. Automated Data Cleaning & EDA Pipeline (Python / SQL)", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 4.5, "- Built end-to-end Python script utilizing Pandas & SQL queries to clean multi-source datasets.\n- Derived actionable business metrics and visualized trends in Power BI dashboards.")
            pdf.ln(3)

            pdf.set_font("Helvetica", "B", 9.5)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 6, "2. Executive Sales & Performance Dashboard (Power BI / Excel)", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 4.5, "- Designed interactive visual reports displaying KPI metrics, regional performance breakdown, and forecast modeling.\n- Optimized data loading speed and automated recurring weekly refresh schedules.")
            pdf.ln(4)

            # Section: Education & Certification
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(16, 185, 129)
            pdf.cell(0, 7, "EDUCATION & CERTIFICATIONS", ln=True)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(0, 5, "Bachelor of Technology / Science (Data Analytics Focus)", ln=True)
            pdf.cell(0, 5, "Certifications: Python Data Science, Advanced SQL Querying & Power BI Desktop", ln=True)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pdf.output(str(output_path))
            logger.info(f"Generated PDF Resume successfully at {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate PDF resume: {e}")
            raise e

    @classmethod
    def generate_cover_letter_pdf(
        cls,
        cand_name: str,
        company: str,
        job_title: str,
        cover_text: str,
        output_path: Path
    ) -> Path:
        """
        Builds a styled Cover Letter PDF document.
        """
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            clean_name = sanitize_pdf_text(cand_name or "Applicant")
            clean_comp = sanitize_pdf_text(company or "Hiring Manager")
            clean_role = sanitize_pdf_text(job_title or "Job Position")
            clean_text = sanitize_pdf_text(cover_text or "")
            
            # Header
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(16, 24, 40)
            pdf.cell(0, 10, f"COVER LETTER - {clean_role.upper()}", ln=True, align="L")
            
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(0, 6, f"Candidate: {clean_name} | Target Company: {clean_comp}", ln=True, align="L")
            pdf.ln(3)
            
            # Horizontal Divider Line
            pdf.set_draw_color(99, 102, 241)
            pdf.set_line_width(0.8)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(8)
            
            # Main Cover Letter Text Body
            pdf.set_font("Helvetica", "", 10.5)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(0, 6, clean_text)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pdf.output(str(output_path))
            logger.info(f"Generated Cover Letter PDF at {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate Cover Letter PDF: {e}")
            raise e

    @classmethod
    def generate_hr_email_pdf(
        cls,
        cand_name: str,
        company: str,
        job_title: str,
        email_subject: str,
        email_body: str,
        output_path: Path
    ) -> Path:
        """
        Builds a styled HR Recruiter Email PDF document.
        """
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            clean_name = sanitize_pdf_text(cand_name or "Applicant")
            clean_comp = sanitize_pdf_text(company or "Company")
            clean_role = sanitize_pdf_text(job_title or "Job Position")
            clean_sub = sanitize_pdf_text(email_subject or f"Application for {clean_role} - {clean_name}")
            clean_body = sanitize_pdf_text(email_body or "")
            
            # Header
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(16, 24, 40)
            pdf.cell(0, 10, "HR RECRUITER EMAIL DRAFT", ln=True, align="L")
            
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(0, 6, f"Candidate: {clean_name} | Role: {clean_role} | Target Company: {clean_comp}", ln=True, align="L")
            pdf.ln(3)
            
            # Horizontal Divider Line
            pdf.set_draw_color(99, 102, 241)
            pdf.set_line_width(0.8)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(6)
            
            # Subject Box
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(99, 102, 241)
            pdf.cell(0, 6, f"Subject: {clean_sub}", ln=True)
            pdf.ln(4)
            
            # Email Body
            pdf.set_font("Helvetica", "", 10.5)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(0, 6, clean_body)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pdf.output(str(output_path))
            logger.info(f"Generated HR Email PDF at {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate HR Email PDF: {e}")
            raise e

    @classmethod
    def generate_combined_application_pdf(
        cls,
        profile: CandidateProfile,
        company: str,
        job_title: str,
        cover_text: str,
        output_path: Path
    ) -> Path:
        """
        Builds a single combined PDF document containing Cover Letter (Page 1) and Candidate Resume (Page 2+).
        """
        try:
            # 1. Generate Cover Letter PDF to temporary file
            temp_cover_path = settings.EXPORTS_DIR / f"temp_cover_{output_path.name}"
            cls.generate_cover_letter_pdf(
                cand_name=profile.name if profile else "Candidate",
                company=company,
                job_title=job_title,
                cover_text=cover_text,
                output_path=temp_cover_path
            )

            # 2. Check if candidate's original resume PDF exists
            original_resume_pdf = settings.DATA_DIR / "resume.pdf"
            temp_resume_path = None
            if not original_resume_pdf.exists() or not original_resume_pdf.is_file():
                temp_resume_path = settings.EXPORTS_DIR / f"temp_resume_{output_path.name}"
                cls.generate_pdf(profile or CandidateProfile(), temp_resume_path)
                original_resume_pdf = temp_resume_path

            # 3. Merge Cover Letter PDF + Original Resume PDF using pypdf.PdfWriter
            from pypdf import PdfWriter
            merger = PdfWriter()
            merger.append(str(temp_cover_path))
            merger.append(str(original_resume_pdf))
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f_out:
                merger.write(f_out)
            merger.close()
            
            # Clean up temp files
            if temp_cover_path.exists():
                try: temp_cover_path.unlink()
                except: pass
            if temp_resume_path and temp_resume_path.exists():
                try: temp_resume_path.unlink()
                except: pass

            logger.info(f"Generated Combined Application PDF (Cover Letter + Resume) at {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate Combined Application PDF: {e}")
            raise e



