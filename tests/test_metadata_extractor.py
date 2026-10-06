"""
Unit tests for JobMetadataExtractor, company/location/work-mode/employment-type normalization,
and stable deterministic job_id generation.
"""

import pytest
from app.models.job import RawSearchResult, Job
from app.services.url_validator import normalize_canonical_url
from app.services.metadata_extractor import (
    JobMetadataExtractor,
    normalize_company_name,
    normalize_location_name,
    normalize_work_mode,
    normalize_employment_type,
    generate_stable_job_id
)


def test_company_normalization():
    assert normalize_company_name("ABC Pvt. Ltd.") == "abc"
    assert normalize_company_name("ABC Private Limited") == "abc"
    assert normalize_company_name("Acme Technologies Inc.") == "acme"
    assert normalize_company_name("Acme Tech Ltd") == "acme"


def test_location_normalization():
    assert normalize_location_name("Surat, Gujarat, India") == "surat, gujarat"
    assert normalize_location_name("Surat, Gujarat") == "surat, gujarat"
    assert normalize_location_name("Bangalore, Karnataka, IND") == "bangalore, karnataka"
    assert normalize_location_name("") == "unknown"


def test_work_mode_normalization():
    assert normalize_work_mode("Remote / WFH opportunity") == "Remote"
    assert normalize_work_mode("Work From Home position") == "Remote"
    assert normalize_work_mode("Hybrid work model") == "Hybrid"
    assert normalize_work_mode("Onsite in office") == "Onsite"
    assert normalize_work_mode("Unspecified location") == "Unknown"


def test_employment_type_normalization():
    assert normalize_employment_type("Full Time Data Analyst") == "Full-time"
    assert normalize_employment_type("Summer Internship 2026") == "Internship"
    assert normalize_employment_type("Part-time contractor") == "Part-time"
    assert normalize_employment_type("Freelance contract") == "Contract"
    assert normalize_employment_type("General position") == "Unknown"


def test_stable_job_id_generation():
    id1 = generate_stable_job_id("Data Analyst", "ABC Corp", "Surat", "https://linkedin.com/jobs/view/1234")
    id2 = generate_stable_job_id("Data Analyst", "ABC Corp", "Surat", "https://linkedin.com/jobs/view/1234")
    id3 = generate_stable_job_id("Data Analyst", "ABC Corp", "Surat", "https://linkedin.com/jobs/view/9999")
    
    assert id1 == id2
    assert id1 != id3
    assert id1.startswith("job_")


def test_metadata_extraction_schema_org_job_posting():
    extractor = JobMetadataExtractor()
    
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "JobPosting",
          "title": "Senior Data Analyst",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Acme Corp Pvt Ltd"
          },
          "jobLocation": {
            "@type": "Place",
            "address": {
              "addressLocality": "Surat",
              "addressRegion": "Gujarat"
            }
          },
          "employmentType": "FULL_TIME",
          "baseSalary": {
            "@type": "MonetaryAmount",
            "currency": "INR",
            "value": {
              "minValue": 500000,
              "maxValue": 800000
            }
          },
          "datePosted": "2026-09-20",
          "description": "Looking for a Data Analyst proficient in Python and SQL."
        }
        </script>
      </head>
    </html>
    """
    
    job = extractor.extract_from_html(html, "https://www.naukri.com/job-listings-123", "Naukri")
    
    assert isinstance(job, Job)
    assert job.title == "Senior Data Analyst"
    assert job.company == "Acme Corp Pvt Ltd"
    assert job.location == "Surat"
    assert job.employment_type == "Full-time"
    assert job.salary_min == 500000.0
    assert job.salary_max == 800000.0
    assert job.posted_date == "2026-09-20"
    assert job.metadata_confidence == 0.95


def test_metadata_extraction_meta_tags_fallback():
    extractor = JobMetadataExtractor()
    
    html = """
    <html>
      <head>
        <title>Software Engineer - Tech Solutions</title>
        <meta property="og:site_name" content="Tech Solutions Inc" />
        <meta property="og:description" content="Build REST APIs using FastAPI and Python." />
      </head>
    </html>
    """
    
    job = extractor.extract_from_html(html, "https://example.com/job/456", "Other")
    
    assert job.title == "Software Engineer - Tech Solutions"
    assert job.company == "Tech Solutions Inc"
    assert "FastAPI" in job.description_snippet
    assert job.metadata_confidence == 0.50


def test_metadata_extraction_missing_fields_stay_none():
    extractor = JobMetadataExtractor()
    html = "<html><head><title>Minimal Job</title></head></html>"
    
    job = extractor.extract_from_html(html, "https://example.com/minimal", "Other")
    
    assert job.salary_min is None
    assert job.salary_max is None
    assert job.posted_date is None


def test_extract_from_search_result():
    extractor = JobMetadataExtractor()
    
    raw_res = RawSearchResult(
        title="Data Analyst at ABC Technologies - Surat",
        url="https://www.linkedin.com/jobs/view/112233?utm_source=google",
        platform="LinkedIn",
        snippet="Hiring Data Analyst with SQL and Python expertise.",
        query="Data Analyst Surat"
    )
    
    job = extractor.extract_from_search_result(raw_res)
    
    assert job.title == "Data Analyst"
    assert job.company == "ABC Technologies"
    assert job.location == "Surat"
    assert "LinkedIn" in job.source_platforms
    assert job.canonical_url == "https://www.linkedin.com/jobs/view/112233"
