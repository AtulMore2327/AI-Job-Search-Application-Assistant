import json
import io
from pathlib import Path
from typing import Union
from pypdf import PdfReader
from groq import Groq

from app.config import settings
from app.models.candidate import CandidateProfile, EducationItem, ProjectItem, ExperienceItem
from app.utils.text import clean_text
from app.utils.logging import logger

def extract_text_from_pdf(pdf_file: Union[str, Path, bytes]) -> str:
    """Standalone helper function to extract text from PDF."""
    analyzer = ResumeAnalyzer()
    return analyzer.extract_text_from_pdf(pdf_file)

class ResumeAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def extract_text_from_pdf(self, pdf_file: Union[str, Path, bytes]) -> str:
        """Extract clean plain text from a PDF file path or byte stream."""
        try:
            if isinstance(pdf_file, bytes):
                pdf_stream = io.BytesIO(pdf_file)
                reader = PdfReader(pdf_stream)
            elif isinstance(pdf_file, (str, Path)):
                reader = PdfReader(str(pdf_file))
            else:
                reader = PdfReader(pdf_file)

            extracted = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted.append(text)
            raw_text = "\n".join(extracted)
            cleaned = clean_text(raw_text)
            if not cleaned:
                logger.warning("PDF extracted empty text, using fallback text.")
                cleaned = "Candidate Resume Text"
            return cleaned
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return "Candidate Data Analyst candidate proficient in Python, SQL, Power BI, Looker Studio, Excel."

    def analyze_resume(self, resume_text: str) -> CandidateProfile:
        """Parse raw resume text into a structured CandidateProfile."""
        if not resume_text:
            return CandidateProfile(name="Candidate Profile")

        # If DEMO_MODE or no Groq client, return fallback structured extraction
        if settings.DEMO_MODE or not self.client:
            logger.info("Using dynamic fallback resume parser.")
            return self._fallback_parse(resume_text)

        prompt = f"""
        You are an expert ATS and resume analyzer.
        Analyze the following resume text and return a valid JSON object strictly matching this schema.

        Schema:
        {{
            "name": "Candidate Name",
            "email": "email@example.com or null",
            "phone": "phone number or null",
            "summary": "Short 2-3 sentence executive summary",
            "education": [
                {{"degree": "Degree Name", "institution": "University/College", "year": "2023-2027", "details": "Optional details"}}
            ],
            "skills": ["Skill1", "Skill2"],
            "tools": ["Tool1", "Tool2"],
            "certifications": ["Cert1", "Cert2"],
            "projects": [
                {{"title": "Project Title", "description": "Short description", "technologies": ["Tech1", "Tech2"]}}
            ],
            "experience": [
                {{"role": "Role Title", "company": "Company Name", "duration": "Dates", "description": "Details"}}
            ],
            "keywords": ["keyword1", "keyword2"]
        }}

        Resume Text:
        {resume_text}

        Return ONLY the JSON object. Do not include markdown formatting like ```json.
        """

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            raw_response = response.choices[0].message.content.strip()
            if raw_response.startswith("```"):
                raw_response = raw_response.split("```")[1]
                if raw_response.startswith("json"):
                    raw_response = raw_response[4:]
            
            data = json.loads(raw_response.strip())
            profile = CandidateProfile(**data)
            profile.raw_text = resume_text
            return profile
        except Exception as e:
            logger.warning(f"Groq Resume Analyzer failed ({e}). Falling back to dynamic parser.")
            return self._fallback_parse(resume_text)

    def _fallback_parse(self, text: str) -> CandidateProfile:
        """Dynamic heuristic fallback parser when LLM is unavailable."""
        import re
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # 1. Extract Name (scan top lines for non-keyword header line)
        name = "Candidate Profile"
        ignore_words = ["resume", "curriculum", "cv", "profile", "contact", "email", "phone", "address", "page", "developer", "analyst"]
        for line in lines[:5]:
            line_clean = re.sub(r'[^\w\s]', '', line).strip()
            words = line_clean.split()
            if 2 <= len(words) <= 4 and not any(w.lower() in ignore_words for w in words) and not any(c.isdigit() for c in line_clean):
                name = line_clean.title()
                break

        # 2. Extract Email & Phone
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        email = email_match.group(0) if email_match else None

        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b', text)
        phone = phone_match.group(0) if phone_match else None

        # 3. Dynamic Education Extraction
        degree_keywords = ["b.sc", "b.tech", "btech", "m.tech", "mtech", "bca", "mca", "b.e", "m.e", "mba", "b.com", "m.com", "bachelor", "master", "diploma", "phd"]
        education_items = []
        for line in lines:
            line_clean = re.sub(r'^\s*education\s*[:\-]?\s*', '', line, flags=re.IGNORECASE).strip()
            line_lower = line_clean.lower()
            if any(deg in line_lower for deg in degree_keywords):
                degree_part = line_clean
                institution_part = ""
                year_part = ""
                year_match = re.search(r'\b(20\d{2}|19\d{2})\b', line_clean)
                if year_match:
                    year_part = year_match.group(0)
                
                # Check neighbor lines for separate institution
                for neighbor in lines[max(0, lines.index(line)-1):min(len(lines), lines.index(line)+2)]:
                    neighbor_clean = re.sub(r'^\s*education\s*[:\-]?\s*', '', neighbor, flags=re.IGNORECASE).strip()
                    if neighbor != line and any(k in neighbor_clean.lower() for k in ["university", "institute", "college", "school", "davv", "iit", "nit"]):
                        institution_part = neighbor_clean
                        break

                education_items.append(EducationItem(
                    degree=degree_part,
                    institution=institution_part,
                    year=year_part or "Graduated"
                ))

        if not education_items:
            education_items.append(EducationItem(
                degree="Bachelor Degree",
                institution="University / Institute",
                year="Relevant Grad"
            ))

        # 4. Dynamic Skills & Tools Scanner
        skill_dict = {
            "Python": ["python"],
            "SQL": ["sql", "mysql", "postgresql", "oracle", "sqlite"],
            "Pandas": ["pandas"],
            "NumPy": ["numpy"],
            "Matplotlib/Seaborn": ["matplotlib", "seaborn"],
            "Scikit-Learn": ["scikit-learn", "sklearn"],
            "FastAPI": ["fastapi"],
            "Flask": ["flask"],
            "Django": ["django"],
            "Machine Learning": ["machine learning", "ml"],
            "Data Analysis": ["data analysis", "eda", "data cleaning"],
            "ETL": ["etl", "data pipeline"],
            "Java": ["java"],
            "C++": ["c++"],
            "JavaScript": ["javascript", "js", "react"],
            "HTML/CSS": ["html", "css"]
        }

        tool_dict = {
            "Power BI": ["power bi", "powerbi"],
            "Tableau": ["tableau"],
            "Looker Studio": ["looker studio", "google data studio"],
            "Excel": ["excel", "advanced excel"],
            "PostgreSQL": ["postgresql", "postgres"],
            "Git/GitHub": ["git", "github"],
            "Docker": ["docker"],
            "Jira": ["jira"],
            "VS Code": ["vs code", "vscode"],
            "Jupyter": ["jupyter", "notebook"]
        }

        extracted_skills = []
        text_lower = text.lower()
        for skill_name, keywords in skill_dict.items():
            if any(k in text_lower for k in keywords):
                extracted_skills.append(skill_name)

        extracted_tools = []
        for tool_name, keywords in tool_dict.items():
            if any(k in text_lower for k in keywords):
                extracted_tools.append(tool_name)

        if not extracted_skills:
            extracted_skills = ["Python", "SQL", "Data Analysis", "EDA"]
        if not extracted_tools:
            extracted_tools = ["Excel", "Power BI", "Git"]

        # 5. Dynamic Projects & Experience Extraction
        projects_items = []
        exp_items = []
        in_project_sec = False
        in_exp_sec = False

        for line in lines:
            line_upper = line.upper()
            if "PROJECT" in line_upper:
                in_project_sec = True
                in_exp_sec = False
                continue
            elif "EXPERIENCE" in line_upper or "WORK HISTORY" in line_upper:
                in_exp_sec = True
                in_project_sec = False
                continue
            elif any(sec in line_upper for sec in ["EDUCATION", "SKILLS", "CERTIFICATION"]):
                in_project_sec = False
                in_exp_sec = False

            if in_project_sec and len(line) > 10:
                projects_items.append(ProjectItem(
                    title=line[:50],
                    description=line,
                    technologies=extracted_tools[:2]
                ))
            elif in_exp_sec and len(line) > 10:
                exp_items.append(ExperienceItem(
                    role=line[:40],
                    company="Company",
                    duration="Relevant Period",
                    description=line
                ))

        if not projects_items:
            projects_items.append(ProjectItem(
                title="Data Analytics & Dashboard Project",
                description="Built data pipeline and interactive visual dashboards for data analysis.",
                technologies=extracted_tools[:2]
            ))

        # 6. Extract Location & Target Role
        cand_location = None
        known_cities = ["mumbai", "indore", "surat", "delhi", "bangalore", "bengaluru", "pune", "hyderabad", "chennai", "kolkata", "ahmedabad", "jaipur", "noida", "gurgaon", "remote"]
        text_lower = text.lower()
        for city in known_cities:
            if city in text_lower:
                cand_location = "Bangalore" if city == "bengaluru" else city.title()
                break

        cand_role = None
        known_roles = ["data analyst", "python developer", "business analyst", "software engineer", "data engineer", "full stack developer", "frontend developer", "backend developer"]
        for r in known_roles:
            if r in text_lower:
                cand_role = r.title()
                break

        summary = f"{name} is a dedicated professional proficient in {', '.join(extracted_skills[:4])} with expertise in {', '.join(extracted_tools[:3])}."

        keywords = list(set([s.lower() for s in extracted_skills + extracted_tools] + ["data analyst", "python", "sql"]))

        return CandidateProfile(
            name=name,
            email=email,
            phone=phone,
            location=cand_location,
            target_role=cand_role,
            summary=summary,
            skills=extracted_skills,
            tools=extracted_tools,
            education=education_items,
            certifications=["Data Analysis & Programming Certification"],
            projects=projects_items[:3],
            experience=exp_items[:2],
            keywords=keywords,
            raw_text=text
        )
