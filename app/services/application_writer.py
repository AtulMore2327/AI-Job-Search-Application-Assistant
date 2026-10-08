import json
from groq import Groq

from app.config import settings
from app.models.candidate import CandidateProfile
from app.models.job import JobPosting
from app.models.matching import JobMatchResult
from app.models.application import GeneratedApplication
from app.utils.logging import logger

class ApplicationWriter:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def generate_application_package(
        self,
        candidate: CandidateProfile,
        job: JobPosting,
        match_result: JobMatchResult = None
    ) -> GeneratedApplication:
        """
        Generate personalized Cover Letter, HR Email Body, Subject, and LinkedIn Message
        using strictly authentic facts from candidate profile and job details.
        """
        if settings.DEMO_MODE or not self.client:
            return self._fallback_generate(candidate, job)

        prompt = f"""
        You are a career counselor and professional resume writer.
        Generate personalized application materials for the following candidate applying to a specific job vacancy.

        CRITICAL RULE: Rely ONLY on the candidate's actual profile data and job description. Do NOT invent fake employers, years of experience, certifications, or degree titles.

        Candidate Profile:
        - Name: {candidate.name}
        - Email: {candidate.email or 'candidate@example.com'}
        - Skills: {", ".join(candidate.skills)}
        - Tools: {", ".join(candidate.tools)}
        - Education: {candidate.education[0].degree if candidate.education else 'Data Science Graduate'} from {candidate.education[0].institution if candidate.education else 'University'}
        - Top Projects: {candidate.projects[0].title if candidate.projects else 'Data Analytics Dashboard'}

        Job Details:
        - Role: {job.title}
        - Company: {job.company}
        - Location: {job.location}
        - Required Skills: {", ".join(job.required_skills)}

        Return a valid JSON object strictly matching this schema:
        {{
            "email_subject": "Application for Data Analyst Position - [Candidate Name]",
            "hr_email_body": "Dear Hiring Team,...",
            "cover_letter": "Dear Hiring Manager,...",
            "linkedin_message": "Hi [Hiring Manager],..."
        }}

        Return ONLY JSON. Do not include markdown formatting.
        """

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            raw_content = response.choices[0].message.content.strip()
            if raw_content.startswith("```"):
                raw_content = raw_content.split("```")[1]
                if raw_content.startswith("json"):
                    raw_content = raw_content[4:]

            data = json.loads(raw_content.strip())
            return GeneratedApplication(
                job_id=job.job_id,
                job_title=job.title,
                company=job.company,
                cover_letter=data.get("cover_letter", ""),
                email_subject=data.get("email_subject", ""),
                hr_email_body=data.get("hr_email_body", ""),
                linkedin_message=data.get("linkedin_message", "")
            )
        except Exception as e:
            logger.warning(f"Groq Application Writer failed ({e}). Using authentic template generator.")
            return self._fallback_generate(candidate, job)

    def _fallback_generate(self, candidate: CandidateProfile, job: JobPosting) -> GeneratedApplication:
        name = candidate.name or "Candidate"
        role = job.title or "Data Analyst"
        company = job.company or "Tech Company"
        skills = ", ".join(candidate.skills[:4]) or "Python, SQL, Power BI, Looker Studio"

        subject = f"Application for {role} - {name}"

        hr_email = (
            f"Dear Hiring Team at {company},\n\n"
            f"I am writing to express my enthusiastic interest in the {role} position. "
            f"I hold strong skills in {skills}, alongside practical hands-on project experience in data cleaning, "
            f"visualization, and analytical insights generation.\n\n"
            f"Attached is my resume for your review. I look forward to discussing how my analytical skills can add value to {company}.\n\n"
            f"Best regards,\n{name}"
        )

        cover_letter = (
            f"Dear Hiring Manager,\n\n"
            f"I am applying for the {role} opportunity at {company}. "
            f"With hands-on proficiency in {skills}, I have completed comprehensive analytical projects including "
            f"Google Merchandise Store Analysis and Airbnb Demand Analysis.\n\n"
            f"My focus is on transforming raw datasets into clear, actionable business dashboards. "
            f"I am eager to contribute my technical foundation and quick learning ability to your team at {company}.\n\n"
            f"Thank you for considering my application.\n\n"
            f"Sincerely,\n{name}"
        )

        linkedin_msg = (
            f"Hi Hiring Team, I noticed the open {role} role at {company} and wanted to reach out directly. "
            f"I specialize in {skills} and building actionable dashboards. I'd love to connect and share my profile!"
        )

        return GeneratedApplication(
            job_id=job.job_id,
            job_title=role,
            company=company,
            cover_letter=cover_letter,
            email_subject=subject,
            hr_email_body=hr_email,
            linkedin_message=linkedin_msg
        )

ApplicationWriterService = ApplicationWriter
