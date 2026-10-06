import sqlite3
import os
from pathlib import Path
from app.config import settings
from app.utils.logging import logger

def get_db_connection() -> sqlite3.Connection:
    """Connect to local SQLite database and return connection handle."""
    settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite database tables and indices."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop old tables if column mismatch exists to ensure schema integrity
    try:
        cursor.execute("SELECT description FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS jobs")
        cursor.execute("DROP TABLE IF EXISTS job_matches")

    try:
        cursor.execute("SELECT cover_letter FROM applications LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS applications")

    # Candidate Profiles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidate_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        skills_json TEXT,
        summary TEXT,
        profile_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Jobs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        work_mode TEXT,
        employment_type TEXT,
        description TEXT,
        required_skills_json TEXT,
        canonical_url TEXT UNIQUE,
        sources_json TEXT,
        is_duplicate INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Matches Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_matches (
        job_id TEXT PRIMARY KEY,
        job_title TEXT,
        company TEXT,
        match_score REAL,
        breakdown_json TEXT,
        skill_gap_json TEXT,
        explanation TEXT,
        is_preference_match INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(job_id)
    )
    """)

    # Applications Tracker Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        application_id TEXT PRIMARY KEY,
        job_id TEXT,
        company TEXT,
        job_title TEXT,
        status TEXT DEFAULT 'Saved',
        cover_letter TEXT,
        email_subject TEXT,
        hr_email_body TEXT,
        linkedin_message TEXT,
        applied_date TEXT,
        follow_up_date TEXT,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(job_id)
    )
    """)

    conn.commit()
    conn.close()
    logger.info("SQLite database tables initialized successfully.")
