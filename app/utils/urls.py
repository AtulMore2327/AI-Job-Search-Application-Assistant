from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import re

TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'fbclid', 'ref', 'source', 'trk', 'trackingId', 'mid', 'sid'
}

def clean_url(url: str) -> str:
    """Normalize URL and safely strip tracking query parameters."""
    if not url:
        return ""
    url = url.strip()
    if not url.lower().startswith(('http://', 'https://')):
        url = 'https://' + url
        
    parsed = urlparse(url)
    # Filter out tracking query params
    filtered_query = [
        (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    
    # Reconstruct clean URL without trailing slashes in path
    clean_path = parsed.path.rstrip('/')
    if not clean_path:
        clean_path = '/'
        
    clean_query = urlencode(filtered_query)
    
    cleaned = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        clean_path,
        parsed.params,
        clean_query,
        "" # Drop fragment identifiers
    ))
    return cleaned

normalize_url = clean_url

def extract_domain(url: str) -> str:
    """Extract canonical domain name from URL."""
    if not url:
        return ""
    parsed = urlparse(url if url.startswith(('http://', 'https://')) else 'https://' + url)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc

def detect_platform_from_url(url: str) -> str:
    domain = extract_domain(url)
    if "linkedin" in domain:
        return "LinkedIn"
    if "naukri" in domain:
        return "Naukri"
    if "indeed" in domain:
        return "Indeed"
    if "glassdoor" in domain:
        return "Glassdoor"
    if "internshala" in domain:
        return "Internshala"
    return domain.capitalize() if domain else "Unknown"

def classify_url_type(url: str, title: str = "", content: str = "") -> str:
    """
    Classify URL page type into:
    INDIVIDUAL_JOB, LISTING_PAGE, COMPANY_PAGE, SEARCH_PAGE, INVALID, UNKNOWN
    """
    if not url or not url.startswith(('http://', 'https://')):
        return "INVALID"
        
    domain = extract_domain(url)
    url_lower = url.lower()
    title_lower = title.lower()
    
    # Platform specific patterns for individual jobs vs search listings
    if "linkedin.com" in domain:
        if "/jobs/view/" in url_lower or "currentjobid=" in url_lower:
            return "INDIVIDUAL_JOB"
        if "/jobs/search" in url_lower:
            return "LISTING_PAGE"
            
    if "naukri.com" in domain:
        if "-jobs-in-" in url_lower or "search" in url_lower or "job-listings-" in url_lower and "jobs-in" in url_lower:
            return "LISTING_PAGE"
        if "job-listings-" in url_lower or "-job-" in url_lower:
            return "INDIVIDUAL_JOB"
            
    if "indeed.com" in domain:
        if "/viewjob" in url_lower or "jk=" in url_lower:
            return "INDIVIDUAL_JOB"
        if "/q-" in url_lower or "/jobs" in url_lower:
            return "LISTING_PAGE"
            
    if "glassdoor.com" in domain or "glassdoor.co.in" in domain:
        if "/job-listing/" in url_lower or "joblistingId=" in url_lower:
            return "INDIVIDUAL_JOB"
            
    if "internshala.com" in domain:
        if "/internship/detail/" in url_lower or "/job/detail/" in url_lower:
            return "INDIVIDUAL_JOB"
        return "LISTING_PAGE"

    # Title indicators
    listing_title_triggers = ["vacancies", "open roles", "jobs in", "latest", "search", "browse"]
    if any(trigger in title_lower for trigger in listing_title_triggers):
        return "LISTING_PAGE"
        
    # Default fallback heuristics
    if any(k in url_lower for k in ["/view/", "/detail/", "/job/", "/position/", "/career/"]):
        return "INDIVIDUAL_JOB"
        
    return "INDIVIDUAL_JOB"
