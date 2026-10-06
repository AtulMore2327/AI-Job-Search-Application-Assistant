import json
import uuid
from typing import List, Optional, Dict
from app.database.db import get_db_connection
from app.models.candidate import CandidateProfile
from app.models.job import JobPosting
from app.models.matching import JobMatchResult
from app.models.application import GeneratedApplication, ApplicationTrackerItem, ApplicationStatus

class DatabaseRepository:
    @staticmethod
    def save_candidate_profile(profile: CandidateProfile) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO candidate_profiles (name, skills_json, summary, profile_json) VALUES (?, ?, ?, ?)",
            (
                profile.name,
                json.dumps(profile.skills),
                profile.summary,
                profile.model_dump_json()
            )
        )
        profile_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return profile_id

    @staticmethod
    def save_jobs(jobs: List[JobPosting]):
        conn = get_db_connection()
        cursor = conn.cursor()
        for job in jobs:
            cursor.execute("""
            INSERT OR REPLACE INTO jobs 
            (job_id, title, company, location, work_mode, employment_type, description, required_skills_json, canonical_url, sources_json, is_duplicate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.title,
                job.company,
                job.location,
                job.work_mode,
                job.employment_type,
                job.description,
                json.dumps(job.required_skills),
                job.canonical_url,
                json.dumps([s.model_dump() for s in job.sources]),
                1 if job.is_duplicate else 0
            ))
        conn.commit()
        conn.close()

    @staticmethod
    def save_job_matches(matches: List[JobMatchResult]):
        conn = get_db_connection()
        cursor = conn.cursor()
        for match in matches:
            cursor.execute("""
            INSERT OR REPLACE INTO job_matches
            (job_id, job_title, company, match_score, breakdown_json, skill_gap_json, explanation, is_preference_match)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match.job_id,
                match.job_title,
                match.company,
                match.match_score,
                match.breakdown.model_dump_json(),
                match.skill_gap.model_dump_json(),
                match.explanation,
                1 if match.is_preference_match else 0
            ))
        conn.commit()
        conn.close()

    @staticmethod
    def save_application(app: GeneratedApplication) -> str:
        conn = get_db_connection()
        cursor = conn.cursor()
        app_id = str(uuid.uuid4())[:8]
        cursor.execute("""
        INSERT OR REPLACE INTO applications
        (application_id, job_id, company, job_title, status, cover_letter, email_subject, hr_email_body, linkedin_message, notes)
        VALUES (?, ?, ?, ?, 'Saved', ?, ?, ?, ?, ?)
        """, (
            app_id,
            app.job_id,
            app.company,
            app.job_title,
            app.cover_letter,
            app.email_subject,
            app.hr_email_body,
            app.linkedin_message,
            app.notes or ""
        ))
        conn.commit()
        conn.close()
        return app_id

    @staticmethod
    def get_all_applications() -> List[Dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def update_application_status(app_id: str, status: str, notes: Optional[str] = None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if notes is not None:
            cursor.execute(
                "UPDATE applications SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE application_id = ?",
                (status, notes, app_id)
            )
        else:
            cursor.execute(
                "UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE application_id = ?",
                (status, app_id)
            )
        conn.commit()
        conn.close()

CandidateRepository = DatabaseRepository
JobRepository = DatabaseRepository
MatchRepository = DatabaseRepository
ApplicationRepository = DatabaseRepository
JDCacheRepository = DatabaseRepository
MatchCacheRepository = DatabaseRepository
