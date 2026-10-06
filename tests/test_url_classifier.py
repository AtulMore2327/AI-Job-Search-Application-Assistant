import pytest
from app.utils.urls import classify_url_type
from app.models.job import JobSource
from app.services.url_validator import URLValidator

def test_classify_individual_vs_listing():
    assert classify_url_type("https://www.linkedin.com/jobs/view/1234567") == "INDIVIDUAL_JOB"
    assert classify_url_type("https://in.indeed.com/viewjob?jk=87f0ce031122") == "INDIVIDUAL_JOB"
    assert classify_url_type("https://www.naukri.com/data-analyst-jobs-in-surat", title="50 Data Analyst Jobs") == "LISTING_PAGE"

def test_url_validator_filters_listings():
    sources = [
        JobSource(platform="LinkedIn", url="https://in.linkedin.com/jobs/view/12345", title="Data Analyst Job"),
        JobSource(platform="Shine", url="https://www.shine.com/job-search/data-analyst-jobs-in-surat", title="50+ Data Analyst Jobs in Surat")
    ]
    individual, rejected = URLValidator.validate_and_classify_sources(sources)
    assert len(individual) == 1
    assert len(rejected) == 1
    assert individual[0].platform == "LinkedIn"
