"""
SQLite Database connection management and table schema initialization.
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from app.config import get_settings, BASE_DIR
from app.utils.logging import get_logger

logger = get_logger("database_connection")


def resolve_db_path(db_url: str = None) -> str:
    """Resolve sqlite database file path from config URL."""
    settings = get_settings()
    url = db_url or settings.DATABASE_URL
    
    if url == ":memory:" or url.startswith("sqlite:///:memory:"):
        return ":memory:"
        
    if url.startswith("sqlite:///"):
        path_str = url.replace("sqlite:///", "")
    else:
        path_str = url

    db_path = Path(path_str)
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)


@contextmanager
def get_db_connection(db_path: str = None) -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional SQLite database connection context."""
    target_path = resolve_db_path(db_path)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error: {e}")
        raise
    finally:
        conn.close()


def init_db(db_path: str = None):
    """Initialize SQLite database tables and indexes."""
    target_path = resolve_db_path(db_path)
    logger.info(f"Initializing SQLite database schema at: {target_path}")

    with get_db_connection(target_path) as conn:
        cursor = conn.cursor()

        # 1. Candidates table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            location TEXT,
            summary TEXT,
            profile_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        # 2. Jobs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            work_mode TEXT,
            employment_type TEXT,
            canonical_url TEXT NOT NULL,
            job_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        # 3. JD Analysis Cache table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jd_cache (
            job_id TEXT PRIMARY KEY,
            raw_jd_text TEXT,
            jd_analysis_json TEXT NOT NULL,
            extracted_at TEXT NOT NULL
        )
        """)

        # 4. Match Result Cache table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_cache (
            cache_key TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            match_score REAL NOT NULL,
            match_result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        # 5. Applications Tracker table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            application_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            candidate_name TEXT NOT NULL,
            company TEXT NOT NULL,
            job_title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'SAVED',
            notes TEXT DEFAULT '',
            applied_date TEXT,
            package_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        # 6. User Preferences table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id TEXT PRIMARY KEY,
            target_role TEXT NOT NULL,
            preferences_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        # Indexes for fast querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_apps_status ON applications(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_apps_job_id ON applications(job_id)")

        logger.info("Database schema initialized successfully.")


def check_db_health(db_path: str = None) -> bool:
    """Verify database connectivity and query execution."""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

