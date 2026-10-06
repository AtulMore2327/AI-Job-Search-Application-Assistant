"""
Demo Service for AI Job Search & Application Assistant.
Provides deterministic, high-quality demonstration data when DEMO_MODE=True or when API keys are unconfigured.
All demo data is clearly labeled with '[DEMO DATA]' to prevent confusion with real vacancies or credentials.
"""

from typing import List, Optional
from datetime import datetime, timezone
from app.models.candidate import CandidateProfile, ExperienceItem, EducationItem, ProjectItem
from app.models.job import Job, RawSearchResult, DiscoveryResult, JDAnalysis, JDExtractResult
from app.models.matching import MatchResult, SkillMatch, SkillGap
from app.models.application import ApplicationPackage, CoverLetter, EmailDraft, LinkedInMessage
from app.models.tracker import TrackedApplication, TrackerStats
from app.utils.logging import get_logger

logger = get_logger("demo_service")

class DemoService:
    """Provides safe, offline, deterministic demo responses for all pipeline stages."""

    @staticmethod
    def get_demo_candidate_profile() -> CandidateProfile:
        """Return a complete sample candidate profile labeled as Demo Data."""
        return CandidateProfile(
            name="Alex Mercer [DEMO CANDIDATE]",
            email="alex.mercer.demo@example.com",
            phone="+1 (555) 019-2831",
            location="Bengaluru, India",
            summary="Detail-oriented Data Analyst & Software Developer with 3+ years of experience in Python, SQL, data modeling, and web applications. Proven track record in automated pipeline building and insights dashboards.",
            skills=["Python", "SQL", "Pandas", "Power BI", "FastAPI", "Machine Learning", "Git", "REST APIs"],
            tools=["Power BI", "Git", "Docker", "VS Code", "Jira", "PostgreSQL"],
            certifications=["Certified Data Analyst Professional (Demo)", "Python Specialist (Demo)"],
            experience=[
                ExperienceItem(
                    title="Data Analyst (Demo)",
                    company="Acme Analytics Demo Corp",
                    duration="2022 - Present",
                    responsibilities=[
                        "Built SQL & Python pipelines processing over 500k records daily",
                        "Designed executive Power BI dashboards improving decision efficiency by 25%",
                        "Collaborated with cross-functional teams to automate weekly client reporting"
                    ],
                    technologies=["Python", "SQL", "Power BI", "PostgreSQL"]
                ),
                ExperienceItem(
                    title="Junior Developer (Demo)",
                    company="DemoTech Software Solutions",
                    duration="2021 - 2022",
                    responsibilities=[
                        "Developed backend REST API endpoints using Python and FastAPI",
                        "Optimized database queries reducing average response times by 30%"
                    ],
                    technologies=["Python", "FastAPI", "Git"]
                )
            ],
            education=[
                EducationItem(
                    degree="Bachelor of Technology in Computer Science",
                    institution="National Institute of Technology (Demo Univ)",
                    year="2021",
                    grade="3.8 / 4.0"
                )
            ],
            projects=[
                ProjectItem(
                    title="Automated Job Matching Dashboard [DEMO]",
                    description="Built an end-to-end data pipeline & dashboard matching candidate skills with vacancy descriptions.",
                    technologies=["Python", "FastAPI", "SQL", "Power BI"]
                )
            ]
        )


    @staticmethod
    def get_demo_jobs() -> List[Job]:
        """Return a list of curated demo jobs labeled clearly as Demo Data."""
        now_iso = datetime.now(timezone.utc).isoformat()
        return [
            Job(
                job_id="demo-job-101",
                title="Python Backend Developer",
                company="DemoTech",
                location="Indore",
                work_mode="On-site",
                employment_type="Full Time",
                experience_level="Mid",
                salary_min=1000000,
                salary_max=1500000,
                currency="INR",
                description_snippet="DEMO DATA: Seeking a Python Backend Developer skilled in FastAPI, PostgreSQL, Redis, and asynchronous microservices.",
                skills=["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
                source_platforms=["Naukri (Demo)"],
                source_urls=["https://demo.example.com/jobs/demotech-python-dev"],
                canonical_url="https://demo.example.com/jobs/demotech-python-dev",
                posted_date="2026-09-22",
                discovered_at=now_iso,
                metadata_confidence=0.95
            ),
            Job(
                job_id="demo-job-102",
                title="Data Analyst",
                company="Acme Demo Corp",
                location="Indore",
                work_mode="Hybrid",
                employment_type="Full Time",
                experience_level="Mid",
                salary_min=1200000,
                salary_max=1800000,
                currency="INR",
                description_snippet="DEMO DATA: Acme Demo Corp is hiring a Data Analyst proficient in Python, SQL, Power BI, and data warehousing to lead business intelligence analytics.",
                skills=["Python", "SQL", "Power BI", "Data Modeling", "ETL"],
                source_platforms=["LinkedIn (Demo)"],
                source_urls=["https://demo.example.com/jobs/acme-data-analyst"],
                canonical_url="https://demo.example.com/jobs/acme-data-analyst",
                posted_date="2026-09-20",
                discovered_at=now_iso,
                metadata_confidence=0.95
            ),
            Job(
                job_id="demo-job-103",
                title="Junior Data Analyst",
                company="XYZ Demo Company",
                location="Indore",
                work_mode="On-site",
                employment_type="Full Time",
                experience_level="Junior",
                salary_min=600000,
                salary_max=900000,
                currency="INR",
                description_snippet="DEMO DATA: XYZ Demo Company is looking for a Junior Data Analyst to perform data cleaning, visualization, and SQL reporting.",
                skills=["SQL", "Python", "Excel", "Data Cleaning"],
                source_platforms=["Indeed (Demo)"],
                source_urls=["https://demo.example.com/jobs/xyz-junior-data-analyst"],
                canonical_url="https://demo.example.com/jobs/xyz-junior-data-analyst",
                posted_date="2026-09-21",
                discovered_at=now_iso,
                metadata_confidence=0.90
            )
        ]

    @classmethod
    def get_demo_discovery_result(cls) -> DiscoveryResult:
        """Return complete DiscoveryResult containing demo search results."""
        jobs = cls.get_demo_jobs()
        raw_results = [
            RawSearchResult(
                title=f"{j.title} at {j.company} - {j.location}",
                url=j.canonical_url,
                platform=j.source_platforms[0] if j.source_platforms else "LinkedIn (Demo)",
                snippet=j.description_snippet,
                score=0.95,
                query="demo search query",
                raw_data={
                    "company": j.company,
                    "location": j.location,
                    "work_mode": j.work_mode,
                    "employment_type": j.employment_type,
                    "salary_min": j.salary_min,
                    "salary_max": j.salary_max,
                    "currency": j.currency
                }
            )
            for j in jobs
        ]
        return DiscoveryResult(
            total_results=len(raw_results),
            successful_queries=3,
            failed_queries=0,
            platform_counts={"LinkedIn (Demo)": 1, "Naukri (Demo)": 1, "Indeed (Demo)": 1},
            results=raw_results,
            errors=[]
        )


    @classmethod
    def get_demo_jd_analysis(cls, job_id: str = "demo-job-101") -> JDAnalysis:
        """Return structured demo JD Analysis."""
        return JDAnalysis(
            job_id=job_id,
            title="Demo Senior Data Analyst",
            company="Acme Demo Corp",
            location="Bengaluru, India",
            responsibilities=[
                "Analyze large relational datasets using SQL and Python to extract business insights",
                "Design and maintain interactive Power BI and Tableau dashboards for executive teams",
                "Develop automated data quality checks and ETL pipelines",
                "Present analytical findings and optimization recommendations to stakeholders"
            ],
            required_skills=["Python", "SQL", "Power BI", "Data Analysis", "ETL"],
            preferred_skills=["Spark", "PostgreSQL", "AWS", "Git"],
            technical_skills=["Python", "SQL", "Power BI", "Pandas", "PostgreSQL"],
            soft_skills=["Communication", "Problem Solving", "Stakeholder Management"],
            qualifications=["B.Tech / B.E. / B.Sc in Computer Science or related field"],
            education_requirements="Bachelor's Degree in Computer Science or quantitative field",
            experience_requirements="2-4 years of hands-on data analytics experience",
            employment_type="Full-time",
            work_mode="Hybrid",
            salary_information="₹12,00,000 - ₹18,00,000 PA",
            benefits=["Health Insurance", "Flexible Work Hours", "Learning Allowance"],
            keywords=["Data Analyst", "Python", "SQL", "Power BI", "Business Intelligence"],
            seniority_level="Mid-Senior Level",
            industry="Information Technology & Services",
            summary="[DEMO DATA] Acme Demo Corp seeks a Data Analyst to translate business requirements into actionable insights using SQL, Python, and Power BI dashboards.",
            raw_jd_text="DEMO DATA: Acme Demo Corp is seeking a Senior Data Analyst. Requirements: Python, SQL, Power BI..."
        )

    @classmethod
    def get_demo_match_result(cls, job_id: str = "demo-job-101") -> MatchResult:
        """Return deterministic demo match result."""
        gap = cls.get_demo_skill_gap(job_id=job_id)
        return MatchResult(
            job_id=job_id,
            candidate_name="Alex Mercer [DEMO CANDIDATE]",
            match_score=85.0,
            score_breakdown={
                "required_skills": 35.0,
                "preferred_skills": 10.0,
                "experience": 13.5,
                "education": 10.0,
                "location": 5.0,
                "work_mode": 4.0,
                "employment_type": 5.0,
                "other": 2.5
            },
            matched_required_skills=["Python", "SQL", "Power BI"],
            missing_required_skills=["ETL"],
            matched_preferred_skills=["PostgreSQL", "Git"],
            missing_preferred_skills=["Spark", "AWS"],
            partial_matches=[
                {"candidate_skill": "Pandas", "required_skill": "Data Analysis", "status": "partial", "reason": "Data manipulation library aligns with analysis"}
            ],
            experience_match={"status": "passed", "score": 13.5, "reason": "3+ years experience aligns well with mid-level requirement"},
            education_match={"status": "passed", "score": 10.0, "reason": "B.Tech in Computer Science meets education criteria"},
            location_match={"status": "passed", "score": 5.0, "reason": "Bengaluru location matches posting"},
            work_mode_match={"status": "passed", "score": 4.0, "reason": "Hybrid preference matches job requirement"},
            employment_type_match={"status": "passed", "score": 5.0, "reason": "Full-time requirement matches preference"},
            strengths=[
                "Strong core technical alignment in Python, SQL, and Power BI",
                "Degree in Computer Science aligns well with qualifications",
                "Location and employment type match job requirements"
            ],
            concerns=[
                "Limited explicit experience with distributed ETL tools like Apache Spark"
            ],
            skill_gap=gap,
            explanation="[DEMO DATA] Strong overall alignment (85/100). The candidate possesses all core required skills (Python, SQL, Power BI) and meets location/education criteria."
        )

    @classmethod
    def get_demo_skill_gap(cls, job_id: str = "demo-job-101") -> SkillGap:
        """Return sample skill gap analysis."""
        return SkillGap(
            job_id=job_id,
            candidate_name="Alex Mercer [DEMO CANDIDATE]",
            target_role="Demo Senior Data Analyst",
            critical_gaps=["ETL Pipeline Architecture"],
            secondary_gaps=["Apache Spark", "AWS Redshift"],
            partial_gaps=["Data Analysis (Practicing with Pandas)"],
            matched_skills=["Python", "SQL", "Power BI", "PostgreSQL", "Git"],
            learning_suggestions=[
                "Learn Apache Spark for large-scale distributed data processing",
                "Study cloud data warehousing concepts (AWS Redshift / Snowflake)",
                "Build an end-to-end Airflow or Prefect ETL pipeline project"
            ]
        )

    @classmethod
    def get_demo_application_package(cls, job_id: str = "demo-job-101", company: str = "Acme Demo Corp", job_title: str = "Demo Senior Data Analyst") -> ApplicationPackage:
        """Return complete demo ApplicationPackage."""
        return ApplicationPackage(
            job_id=job_id,
            candidate_name="Alex Mercer [DEMO CANDIDATE]",
            company=company,
            job_title=job_title,
            cover_letter=CoverLetter(
                job_id=job_id,
                candidate_name="Alex Mercer [DEMO CANDIDATE]",
                company=company,
                job_title=job_title,
                greeting="Dear Hiring Manager,",
                opening=f"I am writing to express my enthusiastic interest in the {job_title} position at {company}.",
                body=f"With 3+ years of experience leveraging Python, SQL, and Power BI to analyze complex datasets and automate business reporting, I have successfully delivered high-impact analytics solutions. At my previous position, I engineered automated SQL and Python pipelines that optimized data processing by 25%. My background in computer science equips me to bring immediate value to {company}'s analytics team.",
                closing="Thank you for considering my application. I look forward to discussing how my technical skills and analytical background align with your goals.",
                signature="Sincerely,\nAlex Mercer",
                full_text=f"Dear Hiring Manager,\n\nI am writing to express my enthusiastic interest in the {job_title} position at {company}.\n\nWith 3+ years of experience leveraging Python, SQL, and Power BI to analyze complex datasets and automate business reporting, I have successfully delivered high-impact analytics solutions. At my previous position, I engineered automated SQL and Python pipelines that optimized data processing by 25%. My background in computer science equips me to bring immediate value to {company}'s analytics team.\n\nThank you for considering my application. I look forward to discussing how my technical skills and analytical background align with your goals.\n\nSincerely,\nAlex Mercer"
            ),
            email_draft=EmailDraft(
                job_id=job_id,
                recipient_name="Hiring Team at " + company,
                subject=f"Application for {job_title} - Alex Mercer",
                body=f"Dear Hiring Team,\n\nI have submitted my application for the {job_title} role at {company}. With expertise in Python, SQL, and Power BI dashboards, I am excited about the opportunity to contribute to your analytics initiatives.\n\nAttached is my resume for your review. I look forward to connecting.\n\nBest regards,\nAlex Mercer",
                signature="Alex Mercer | alex.mercer.demo@example.com"
            ),
            linkedin_connection=LinkedInMessage(
                job_id=job_id,
                recipient_name="Recruiter",
                message=f"Hi! I noticed the {job_title} opening at {company}. As a Data Analyst with experience in Python and Power BI, I'd love to connect!",
                character_count=145,
                purpose="connection"
            ),
            linkedin_recruiter=LinkedInMessage(
                job_id=job_id,
                recipient_name="Hiring Lead",
                message=f"Hello! I am reaching out regarding the {job_title} opportunity at {company}. Over the past 3 years, I've built automated Python/SQL analytics pipelines and executive dashboards. I would appreciate the chance to discuss how my skill set aligns with your team's current goals. Thank you!",
                character_count=310,
                purpose="recruiter_outreach"
            ),
            linkedin_followup=LinkedInMessage(
                job_id=job_id,
                recipient_name="Hiring Manager",
                message=f"Hi! Following up on my application for the {job_title} role at {company}. Please let me know if you need any additional information!",
                character_count=138,
                purpose="followup"
            ),
            personalization_points=[
                "Explicitly matched Python, SQL, and Power BI skills",
                "Highlighted 3+ years analytics experience",
                "Referenced Computer Science degree"
            ],
            warnings=[
                "DEMO MODE: Generated content uses fictional candidate and company information for demonstration purposes."
            ]
        )

