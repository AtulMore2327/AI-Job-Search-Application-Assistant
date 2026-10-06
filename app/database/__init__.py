"""
Database module for SQLite persistence, schema initialization, and repositories.
"""

from app.database.connection import get_db_connection, init_db, resolve_db_path
from app.database.repositories import (
    CandidateRepository,
    JobRepository,
    JDCacheRepository,
    MatchCacheRepository,
    ApplicationRepository
)

__all__ = [
    "get_db_connection",
    "init_db",
    "resolve_db_path",
    "CandidateRepository",
    "JobRepository",
    "JDCacheRepository",
    "MatchCacheRepository",
    "ApplicationRepository"
]
