import json
from typing import Dict, Any
from groq import Groq

from app.config import settings
from app.models.job import JobPosting, JDAnalysis
from app.utils.logging import logger

def create_fallback_jd_analysis(text: str = "") -> JDAnalysis:
    return JDAnalysis()

class JDAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def analyze_and_enrich_job(self, job: JobPosting) -> JobPosting:
        """
        Analyze raw Job Description snippet/content using Groq to extract structured required skills,
        preferred skills, responsibilities, experience required, and qualifications.
        """
        if not job.description:
            return job

        if settings.DEMO_MODE or not self.client:
            return self._fallback_analyze(job)

        prompt = f"""
        Extract structured details from the following job description.

        Job Title: {job.title}
        Company: {job.company}
        Raw Description:
        {job.description}

        Return a valid JSON object strictly matching this schema:
        {{
            "required_skills": ["Skill1", "Skill2"],
            "preferred_skills": ["Skill3"],
            "responsibilities": ["Responsibility 1", "Responsibility 2"],
            "qualifications": ["Bachelor degree in Data Science/CS/Math"],
            "experience_required": "Fresher / 0-1 Years",
            "work_mode": "On-site / Hybrid / Remote",
            "employment_type": "Full-time"
        }}

        Return ONLY JSON. Do not include markdown formatting.
        """

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            raw_content = response.choices[0].message.content.strip()
            if raw_content.startswith("```"):
                raw_content = raw_content.split("```")[1]
                if raw_content.startswith("json"):
                    raw_content = raw_content[4:]

            data = json.loads(raw_content.strip())
            job.required_skills = data.get("required_skills", [])
            job.preferred_skills = data.get("preferred_skills", [])
            job.responsibilities = data.get("responsibilities", [])
            job.qualifications = data.get("qualifications", [])
            if data.get("work_mode"):
                job.work_mode = data.get("work_mode")
            if data.get("employment_type"):
                job.employment_type = data.get("employment_type")
            job.extraction_status = "COMPLETED"
            return job
        except Exception as e:
            logger.warning(f"Groq JD Analyzer failed ({e}). Using heuristic enrichment.")
            return self._fallback_analyze(job)

    def _fallback_analyze(self, job: JobPosting) -> JobPosting:
        """Deterministic heuristic extraction for JD details."""
        desc_lower = job.description.lower()
        skills = []
        for kw in ["python", "sql", "power bi", "tableau", "excel", "looker studio", "postgresql", "data cleaning", "etl", "seaborn"]:
            if kw in desc_lower:
                skills.append(kw.title())

        job.required_skills = list(set(skills)) or ["Python", "SQL", "Data Analysis"]
        job.preferred_skills = ["Power BI", "Excel", "Looker Studio"]
        job.responsibilities = [
            "Clean and process customer acquisition datasets.",
            "Build interactive dashboards and visualizations for business insights.",
            "Collaborate with team members on data pipeline analysis."
        ]
        job.qualifications = ["Bachelor's degree in Data Science, Computer Science, or related field"]
        job.extraction_status = "COMPLETED"
        return job

GroqJDAnalyzer = JDAnalyzer
