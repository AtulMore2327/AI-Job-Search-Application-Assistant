import sys
import io

# Force UTF-8 stdout encoding for Windows console compatibility
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import time
from pathlib import Path
from app.config import settings
from app.models.job import JobSearchPreferences
from app.services.resume_analyzer import ResumeAnalyzer
from app.services.query_builder import QueryBuilder
from app.platforms.tavily_adapter import TavilyPlatformAdapter
from app.services.url_validator import URLValidator
from app.services.deduplicator import CrossPlatformDeduplicator
from app.services.jd_analyzer import JDAnalyzer
from app.services.matcher import ResumeJDMatcher
from app.services.skill_gap import SkillGapAnalyzer
from app.services.application_writer import ApplicationWriter
from app.database.db import init_db
from app.database.repositories import DatabaseRepository

def print_step_banner(step_num: int, title: str):
    print(f"\n==========================================================================")
    print(f" [STEP {step_num}]: {title.upper()}")
    print(f"==========================================================================")
    time.sleep(0.3)

def run_step_by_step_demo():
    print("\n>>> STARTING STEP-BY-STEP 10X AI JOB SEARCH & APPLICATION SYSTEM DEMO <<<\n")

    # STEP 1: Configuration & Environment
    print_step_banner(1, "Configuration & Environment Setup")
    print(f"  * Project Name: {settings.PROJECT_NAME}")
    print(f"  * Environment: {'DEMO MODE (Local Datasets)' if settings.DEMO_MODE else 'PRODUCTION MODE (Live APIs)'}")
    print(f"  * Database Target: {settings.DATABASE_PATH}")
    init_db()
    print("  [OK] Step 1 Complete: System initialized.")

    # STEP 2: Resume PDF Upload & Text Parsing
    print_step_banner(2, "Resume Text Extraction & AI Profile Analysis")
    sample_resume = """
    ATUL DEEPAK MORE
    Email: atul.more@example.com | Location: Surat / Indore
    Education: B.Sc. (Data Science) – Devi Ahilya Vishwavidyalaya (2023-2027)
    Technical Skills: Python, SQL, Pandas, NumPy, Feature Engineering, Data Cleaning
    BI Tools: Power BI, Tableau, Looker Studio, Excel, PostgreSQL
    Projects: 
    1. Google Merchandise Store Analysis (Looker Studio)
    2. Airbnb Data Analysis Dashboard (Power BI)
    Experience: Data Analyst Trainee at IANT Institute (July 2025 - Present)
    """
    analyzer = ResumeAnalyzer()
    profile = analyzer.analyze_resume(sample_resume)
    print(f"  * Candidate Name: {profile.name}")
    print(f"  * Extracted Skills: {', '.join(profile.skills)}")
    print(f"  * Extracted Tools: {', '.join(profile.tools)}")
    db_id = DatabaseRepository.save_candidate_profile(profile)
    print(f"  [OK] Step 2 Complete: Profile saved to DB with ID #{db_id}.")

    # STEP 3: Job Preferences & Smart Query Builder
    print_step_banner(3, "User Preferences & Multi-Query Generation")
    prefs = JobSearchPreferences(
        target_role="Data Analyst",
        location="Surat",
        experience_level="Fresher",
        work_mode="On-site",
        employment_type="Full-time",
        result_limit=10
    )
    print(f"  * Preferences: Role='{prefs.target_role}', Location='{prefs.location}', Mode='{prefs.work_mode}'")
    queries = QueryBuilder.build_search_queries(prefs, profile)
    for q_idx, q in enumerate(queries, 1):
        print(f"    Query {q_idx}: {q}")
    print("  [OK] Step 3 Complete: Multi-queries built successfully.")

    # STEP 4: Multi-Platform Job Search
    print_step_banner(4, "Multi-Platform Search Execution (LinkedIn, Naukri, Indeed, Glassdoor)")
    adapter = TavilyPlatformAdapter()
    raw_sources = []
    for q in queries:
        results = adapter.search_jobs(q, prefs)
        raw_sources.extend(results)
    print(f"  * Total Discovered Raw Search Results: {len(raw_sources)}")
    print("  [OK] Step 4 Complete: Search completed.")

    # STEP 5: URL Classification & Filtering
    print_step_banner(5, "URL Classification (Filtering Search Listings vs Individual Jobs)")
    individual_sources, rejected = URLValidator.validate_and_classify_sources(raw_sources)
    print(f"  * Valid Individual Job Postings: {len(individual_sources)}")
    print(f"  * Filtered Generic Listing/Search Pages: {len(rejected)}")
    print("  [OK] Step 5 Complete: Listing pages filtered out.")

    # STEP 6: Cross-Platform Deduplication
    print_step_banner(6, "Cross-Platform Deduplication & Canonical Merging")
    unique_jobs = CrossPlatformDeduplicator.deduplicate_and_normalize(individual_sources)
    print(f"  * Unique Canonical Jobs After Merging: {len(unique_jobs)}")
    for j in unique_jobs:
        platforms = [s.platform for s in j.sources]
        print(f"    - {j.title} at {j.company} (Sources: {', '.join(platforms)})")
    print("  [OK] Step 6 Complete: Duplicates merged.")

    # STEP 7: Job Description Extraction & Enrichment
    print_step_banner(7, "Job Description Scraping & Skill Enrichment")
    jd_analyzer = JDAnalyzer()
    enriched_jobs = []
    for job in unique_jobs:
        enriched = jd_analyzer.analyze_and_enrich_job(job)
        enriched_jobs.append(enriched)
    DatabaseRepository.save_jobs(enriched_jobs)
    print("  [OK] Step 7 Complete: JDs enriched with skills and stored in DB.")

    # STEP 8 & 9: Resume ↔ JD Matcher & Skill Gap
    print_step_banner(8, "Weighted Deterministic Match Scoring & Skill Gap Analysis")
    matches = []
    for job in enriched_jobs:
        res = ResumeJDMatcher.filter_and_match_job(profile, job, prefs)
        matches.append(res)
        print(f"  * Job: '{res.job_title}' at {res.company}")
        print(f"    Match Score: {res.match_score}%")
        print(f"    Matched Skills: {', '.join(res.skill_gap.matched_skills)}")
        if res.skill_gap.missing_must_have:
            print(f"    Missing Must-Have: {', '.join(res.skill_gap.missing_must_have)}")
    DatabaseRepository.save_job_matches(matches)
    print("  [OK] Step 8 & 9 Complete: Match scores & skill gaps calculated.")

    # STEP 10: Application Package Generation
    print_step_banner(10, "Application Package Generation (Cover Letter, HR Email, LinkedIn Msg)")
    writer = ApplicationWriter()
    for job, match_res in zip(enriched_jobs[:2], matches[:2]):
        pkg = writer.generate_application_package(profile, job, match_res)
        app_id = DatabaseRepository.save_application(pkg)
        print(f"  * Generated Package ID #{app_id} for {job.company}:")
        print(f"    Subject: {pkg.email_subject}")
        print(f"    LinkedIn Msg: {pkg.linkedin_message[:80]}...")
    print("  [OK] Step 10 Complete: Application materials written and saved.")

    # STEP 11: Database Persistence Verification
    print_step_banner(11, "SQLite Database & Application Tracker Verification")
    saved_apps = DatabaseRepository.get_all_applications()
    print(f"  * Total Saved Applications in DB: {len(saved_apps)}")
    print("  [OK] Step 11 Complete: SQLite database synced.")

    # STEP 12: Server Launch Instructions
    print_step_banner(12, "FastAPI Application Server Launch")
    print("  * To launch the interactive web dashboard & API server:")
    print("    Command: python run.py")
    print("    URL: http://127.0.0.1:8000")
    print("  [OK] Step 12 Complete: Pipeline step-by-step execution finished successfully!\n")

if __name__ == "__main__":
    run_step_by_step_demo()
