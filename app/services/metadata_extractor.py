"""
Job Metadata Extractor and Normalizer Service.
Extracts structured job metadata from Schema.org JobPosting, meta tags, and page content.
Applies deterministic normalization rules for company, location, work mode, and employment type,
and generates a stable deterministic job_id.
"""

import re
import json
import hashlib
from typing import Optional, Dict, Any, List, Union
from bs4 import BeautifulSoup

from app.models.job import Job, RawSearchResult, URLClassificationResult
from app.services.url_validator import normalize_canonical_url
from app.utils.urls import detect_platform_from_url
from app.utils.text import clean_text, extract_keywords
from app.utils.logging import get_logger

logger = get_logger("metadata_extractor")

# Corporate legal extensions to strip during normalized company comparison
COMPANY_SUFFIXES = [
    r'\bpvt\.?\s*ltd\.?\b', r'\bprivate\s+limited\b', r'\binc\.?\b', r'\bcorp\.?\b',
    r'\bcorporation\b', r'\bllc\.?\b', r'\bltd\.?\b', r'\bco\.?\b', r'\bcompany\b',
    r'\btechnologies\b', r'\btech\b', r'\bsolutions\b', r'\bservices\b', r'\bsoftware\b'
]


def normalize_company_name(company: str) -> str:
    """
    Normalize company name for comparison while preserving raw string.
    Strips corporate legal suffixes and special characters.
    """
    if not company:
        return ""
    
    clean = company.lower().strip()
    for pattern in COMPANY_SUFFIXES:
        clean = re.sub(pattern, '', clean, flags=re.IGNORECASE)
        
    clean = re.sub(r'[^\w\s]', '', clean)
    return re.sub(r'\s+', ' ', clean).strip()


def normalize_location_name(location: str) -> str:
    """
    Normalize location representation for consistent comparison.
    """
    if not location:
        return "unknown"
        
    clean = location.lower().strip()
    # Strip country suffixes if city/state is present
    clean = re.sub(r',\s*(india|ind|us|usa|united states)\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'[^\w\s,]', '', clean)
    return re.sub(r'\s+', ' ', clean).strip()


def normalize_work_mode(text: str) -> str:
    """Normalize work mode string to Onsite, Hybrid, Remote, or Unknown."""
    if not text:
        return "Unknown"
        
    txt = text.lower()
    if any(k in txt for k in ["wfh", "work from home", "remote", "telecommute"]):
        return "Remote"
    elif "hybrid" in txt:
        return "Hybrid"
    elif any(k in txt for k in ["onsite", "on-site", "office", "in-office", "in office"]):
        return "Onsite"
    return "Unknown"


def normalize_employment_type(text: str) -> str:
    """Normalize employment type to Full-time, Internship, Part-time, Contract, or Unknown."""
    if not text:
        return "Unknown"
        
    txt = text.lower()
    if any(k in txt for k in ["full time", "full-time", "full_time", "fulltime", "ft", "permanent"]):
        return "Full-time"
    elif any(k in txt for k in ["internship", "intern", "trainee"]):
        return "Internship"
    elif any(k in txt for k in ["part time", "part-time", "part_time", "parttime", "pt"]):
        return "Part-time"
    elif any(k in txt for k in ["contract", "freelance", "temporary", "temp"]):
        return "Contract"
    return "Unknown"


def generate_stable_job_id(title: str, company: str, location: str, canonical_url: str) -> str:
    """
    Generate a deterministic, stable job ID based on canonical URL or normalized title, company, and location.
    Never uses random UUIDs.
    """
    norm_comp = normalize_company_name(company)
    norm_loc = normalize_location_name(location)
    norm_title = re.sub(r'[^\w\s]', '', title.lower()).strip()
    
    if canonical_url:
        raw_key = f"url:{canonical_url.lower()}"
    else:
        raw_key = f"t:{norm_title}|c:{norm_comp}|l:{norm_loc}"
        
    digest = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:16]
    return f"job_{digest}"


class JobMetadataExtractor:
    """Service to extract metadata from HTML content, raw search results, or URL classification objects."""
    
    def extract_from_html(
        self,
        html_content: str,
        url: str,
        platform: Optional[str] = None
    ) -> Job:
        """
        Extract normalized Job object from raw HTML content.
        
        Args:
            html_content: Raw HTML text string of the job page.
            url: Page URL.
            platform: Platform name if known.
            
        Returns:
            Normalized Job instance.
        """
        canonical = normalize_canonical_url(url)
        detected_platform = platform or detect_platform_from_url(canonical)
        
        title = ""
        company = ""
        location = "Unknown"
        work_mode = "Unknown"
        emp_type = "Unknown"
        salary_min = None
        salary_max = None
        currency = "INR"
        snippet = ""
        posted_date = None
        skills = []
        confidence = 0.50
        raw_meta: Dict[str, Any] = {}

        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # 1. Schema.org JobPosting structured data priority
            json_ld_scripts = soup.find_all("script", type="application/ld+json")
            for script in json_ld_scripts:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        items = data if isinstance(data, list) else [data]
                        for item in items:
                            if isinstance(item, dict) and item.get("@type", "").lower() == "jobposting":
                                raw_meta["schema_job_posting"] = item
                                confidence = 0.95
                                
                                title = item.get("title", title)
                                
                                org = item.get("hiringOrganization")
                                if isinstance(org, dict):
                                    company = org.get("name", company)
                                elif isinstance(org, str):
                                    company = org
                                    
                                loc_item = item.get("jobLocation")
                                if isinstance(loc_item, dict):
                                    addr = loc_item.get("address")
                                    if isinstance(addr, dict):
                                        location = addr.get("addressLocality") or addr.get("addressRegion") or addr.get("name") or location
                                    elif isinstance(addr, str):
                                        location = addr
                                elif isinstance(loc_item, list) and len(loc_item) > 0:
                                    first_loc = loc_item[0]
                                    if isinstance(first_loc, dict):
                                        addr = first_loc.get("address")
                                        if isinstance(addr, dict):
                                            location = addr.get("addressLocality") or location
                                            
                                emp_raw = item.get("employmentType")
                                if isinstance(emp_raw, list):
                                    emp_type = normalize_employment_type(" ".join(emp_raw))
                                elif isinstance(emp_raw, str):
                                    emp_type = normalize_employment_type(emp_raw)
                                    
                                sal_raw = item.get("baseSalary")
                                if isinstance(sal_raw, dict):
                                    currency = sal_raw.get("currency", currency)
                                    val = sal_raw.get("value")
                                    if isinstance(val, dict):
                                        salary_min = val.get("minValue") or val.get("value")
                                        salary_max = val.get("maxValue") or val.get("value")
                                    elif isinstance(val, (int, float)):
                                        salary_min = float(val)
                                        salary_max = float(val)
                                        
                                posted_date = item.get("datePosted")
                                snippet = clean_text(item.get("description", ""))[:300]
                                break
                    except Exception:
                        pass

            # 2. Meta tags & OpenGraph Fallback if title/company missing
            if not title and soup.title and soup.title.string:
                title = soup.title.string.strip()
                
            og_site_name = soup.find("meta", property="og:site_name")
            if not company and og_site_name and og_site_name.get("content"):
                company = og_site_name["content"].strip()

            og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
            if not snippet and og_desc and og_desc.get("content"):
                snippet = clean_text(og_desc["content"])[:300]

        # 3. Clean up Fallbacks if still missing
        if not title:
            # Parse from URL slug fallback
            parsed = urlparse(canonical)
            slug_parts = [p for p in parsed.path.split("/") if p]
            title = slug_parts[-1].replace("-", " ").title() if slug_parts else "Unknown Job Title"
            
        if not company:
            company = detected_platform if detected_platform != "Other" else "Unknown Company"

        # General text normalization
        work_mode = normalize_work_mode(f"{title} {snippet} {location}")
        emp_type = normalize_employment_type(emp_type if emp_type != "Unknown" else f"{title} {snippet}")
        skills = extract_keywords(f"{title} {snippet}")
        
        job_id = generate_stable_job_id(title, company, location, canonical)

        return Job(
            job_id=job_id,
            title=title.strip(),
            company=company.strip(),
            location=location.strip(),
            work_mode=work_mode,
            employment_type=emp_type,
            salary_min=float(salary_min) if salary_min is not None else None,
            salary_max=float(salary_max) if salary_max is not None else None,
            currency=currency,
            description_snippet=snippet,
            skills=skills,
            source_platforms=[detected_platform],
            source_urls=[canonical],
            canonical_url=canonical,
            posted_date=posted_date,
            metadata_confidence=round(confidence, 2),
            raw_metadata=raw_meta
        )

    def extract_from_search_result(self, raw_res: Union[RawSearchResult, URLClassificationResult]) -> Job:
        """
        Create a normalized Job object directly from RawSearchResult or URLClassificationResult.
        """
        url = raw_res.canonical_url if isinstance(raw_res, URLClassificationResult) else raw_res.url
        canonical = normalize_canonical_url(url)
        platform = raw_res.platform or detect_platform_from_url(canonical)
        
        raw_title = raw_res.title if raw_res.title else ""
        snippet = raw_res.snippet if isinstance(raw_res, RawSearchResult) else ""
        raw_data = raw_res.raw_data if isinstance(raw_res, RawSearchResult) and raw_res.raw_data else {}
        
        # Extract title and company from title format e.g. "Data Analyst at ABC Corp - Surat"
        title = raw_title
        company = ""
        location = "Unknown"

        if " at " in raw_title:
            parts = raw_title.split(" at ", 1)
            title = parts[0].strip()
            rest = parts[1]
            if " - " in rest:
                comp_loc = rest.split(" - ", 1)
                company = comp_loc[0].strip()
                location = comp_loc[1].strip()
            elif " in " in rest:
                comp_loc = rest.split(" in ", 1)
                company = comp_loc[0].strip()
                location = comp_loc[1].strip()
            else:
                company = rest.strip()
        elif " - " in raw_title:
            parts = raw_title.split(" - ", 1)
            title = parts[0].strip()
            company = parts[1].strip()

        # Override from raw_data if explicitly provided (e.g. Demo Service metadata)
        if raw_data:
            company = raw_data.get("company", company)
            location = raw_data.get("location", location)

        if not title:
            title = "Unknown Position"
        if not company:
            company = platform if platform != "Other" else "Unknown Company"

        work_mode = raw_data.get("work_mode") or normalize_work_mode(f"{title} {snippet}")
        emp_type = raw_data.get("employment_type") or normalize_employment_type(f"{title} {snippet}")
        salary_min = raw_data.get("salary_min")
        salary_max = raw_data.get("salary_max")
        currency = raw_data.get("currency", "INR")

        skills = extract_keywords(f"{title} {snippet}")
        
        job_id = generate_stable_job_id(title, company, location, canonical)

        return Job(
            job_id=job_id,
            title=title.strip(),
            company=company.strip(),
            location=location.strip(),
            work_mode=work_mode,
            employment_type=emp_type,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            description_snippet=snippet,
            skills=skills,
            source_platforms=[platform],
            source_urls=[canonical],
            canonical_url=canonical,
            metadata_confidence=0.90 if raw_data else 0.75,
            raw_metadata={"raw_title": raw_title, "source_type": type(raw_res).__name__}
        )
