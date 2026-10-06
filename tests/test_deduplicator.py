import pytest
from app.models.job import JobSource
from app.services.deduplicator import CrossPlatformDeduplicator

def test_cross_platform_deduplication():
    sources = [
        JobSource(
            platform="Indeed",
            url="https://in.indeed.com/viewjob?jk=87f0ce031122",
            canonical_url="https://in.indeed.com/viewjob?jk=87f0ce031122",
            title="Data Analyst - Apex Analytics",
            snippet="Data Analyst position in Surat looking for Python and SQL skills."
        ),
        JobSource(
            platform="Naukri",
            url="https://www.naukri.com/job-listings-data-analyst-apex-analytics-surat-1006",
            canonical_url="https://www.naukri.com/job-listings-data-analyst-apex-analytics-surat-1006",
            title="Data Analyst - Apex Analytics Surat",
            snippet="Data Analyst role in Surat with Python and SQL requirements."
        )
    ]

    unique_jobs = CrossPlatformDeduplicator.deduplicate_and_normalize(sources)
    assert len(unique_jobs) == 1
    assert len(unique_jobs[0].sources) == 2
    platforms = [s.platform for s in unique_jobs[0].sources]
    assert "Indeed" in platforms
    assert "Naukri" in platforms
