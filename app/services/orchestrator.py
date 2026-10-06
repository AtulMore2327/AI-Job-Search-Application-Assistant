from typing import Dict, Any, Union, List
from pathlib import Path

from app.models.candidate import CandidateProfile
from app.models.job import JobSearchPreferences, JobPosting, JobSource
from app.services.resume_analyzer import ResumeAnalyzer
from app.services.query_builder import QueryBuilder
from app.platforms.tavily_adapter import TavilyPlatformAdapter
from app.services.url_validator import URLValidator
from app.services.deduplicator import CrossPlatformDeduplicator
from app.services.jd_analyzer import JDAnalyzer
from app.services.matcher import ResumeJDMatcher
from app.services.application_writer import ApplicationWriter
from app.database.db import init_db
from app.database.repositories import DatabaseRepository
from app.utils.logging import logger

class PipelineOrchestrator:
    def __init__(self):
        init_db()
        self.resume_analyzer = ResumeAnalyzer()
        self.search_adapter = TavilyPlatformAdapter()
        self.jd_analyzer = JDAnalyzer()
        self.app_writer = ApplicationWriter()

    def run_pipeline(
        self,
        resume_input: Union[str, Path, bytes, CandidateProfile],
        prefs: JobSearchPreferences,
        is_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Execute full end-to-end 10X AI Job Search & Application Assistant Pipeline.
        """
        logger.info("--- STARTING 10X AI JOB SEARCH PIPELINE ---")
        
        # Step 1 & 2: Resume Parsing & AI Extraction
        if isinstance(resume_input, CandidateProfile):
            profile = resume_input
        elif is_pdf and isinstance(resume_input, (str, Path, bytes)):
            resume_text = self.resume_analyzer.extract_text_from_pdf(resume_input)
            profile = self.resume_analyzer.analyze_resume(resume_text)
        else:
            resume_text = str(resume_input)
            profile = self.resume_analyzer.analyze_resume(resume_text)

        DatabaseRepository.save_candidate_profile(profile)

        # Step 3: Build Multi-Query
        queries = QueryBuilder.build_search_queries(prefs, profile)
        logger.info(f"Generated {len(queries)} dynamic search queries.")

        # Step 4 & 5: Search Platforms
        raw_sources: List[JobSource] = []
        for query in queries:
            results = self.search_adapter.search_jobs(query, prefs)
            raw_sources.extend(results)

        raw_count = len(raw_sources)

        # Step 6, 7, 8: Validate & Classify URLs
        individual_sources, rejected_sources = URLValidator.validate_and_classify_sources(raw_sources)
        individual_count = len(individual_sources)
        invalid_count = len(rejected_sources)

        # Step 9 & 10: Metadata Extraction & Cross-Platform Deduplication with dynamic location
        unique_jobs: List[JobPosting] = CrossPlatformDeduplicator.deduplicate_and_normalize(
            individual_sources,
            default_location=prefs.location if (prefs and prefs.location and prefs.location.strip()) else "India"
        )
        duplicates_removed = individual_count - len(unique_jobs)

        # Step 11 & 12: Full JD Extraction & Enrichment
        enriched_jobs: List[JobPosting] = []
        for job in unique_jobs:
            enriched = self.jd_analyzer.analyze_and_enrich_job(job)
            enriched_jobs.append(enriched)

        DatabaseRepository.save_jobs(enriched_jobs)

        # Step 13, 14, 15: Preference Filtering, Resume-JD Matching & Skill Gap
        matches = []
        applications = []
        preference_matched_count = 0

        for job in enriched_jobs:
            match_res = ResumeJDMatcher.filter_and_match_job(profile, job, prefs)
            matches.append(match_res)
            
            if match_res.is_preference_match:
                preference_matched_count += 1
                # Step 16: Application Package Generation
                app_pkg = self.app_writer.generate_application_package(profile, job, match_res)
                app_id = DatabaseRepository.save_application(app_pkg)
                applications.append({
                    "application_id": app_id,
                    "job_id": job.job_id,
                    "company": job.company,
                    "title": job.title,
                    "match_score": match_res.match_score,
                    "package": app_pkg
                })

        DatabaseRepository.save_job_matches(matches)

        # Real calculated pipeline statistics
        stats = {
            "raw_results_count": raw_count,
            "individual_jobs_count": individual_count,
            "invalid_or_listing_count": invalid_count,
            "duplicates_removed_count": duplicates_removed,
            "unique_jobs_count": len(enriched_jobs),
            "jd_extracted_count": len(enriched_jobs),
            "preference_matches_count": preference_matched_count,
            "application_ready_count": len(applications)
        }

        logger.info(f"Pipeline Completed Successfully! Stats: {stats}")

        return {
            "candidate_profile": profile,
            "preferences": prefs,
            "statistics": stats,
            "jobs": enriched_jobs,
            "match_results": matches,
            "applications": applications
        }

orchestrator = PipelineOrchestrator()
