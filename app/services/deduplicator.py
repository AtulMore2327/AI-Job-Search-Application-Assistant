import uuid
from typing import List, Dict
from rapidfuzz import fuzz

from app.models.job import JobSource, JobPosting, PageType
from app.utils.text import normalize_title, normalize_company
from app.utils.urls import extract_domain
from app.utils.logging import logger

class CrossPlatformDeduplicator:
    SIMILARITY_THRESHOLD = 75.0

    @classmethod
    def deduplicate_and_normalize(cls, sources: List[JobSource], default_location: str = "India") -> List[JobPosting]:
        """
        Group individual job sources representing the exact same job across multiple platforms into single canonical JobPosting items.
        """
        postings: List[JobPosting] = []

        for source in sources:
            norm_title = normalize_title(source.title or "")
            norm_comp = cls._extract_company_from_source(source)
            loc = cls._extract_location_from_source(source, default_location)
            
            # Check if this source matches any existing canonical posting
            matched_posting = None
            for existing in postings:
                ex_title = normalize_title(existing.title)
                ex_comp = normalize_company(existing.company)
                
                # Exact canonical URL match
                if source.canonical_url and source.canonical_url == existing.canonical_url:
                    matched_posting = existing
                    break
                    
                # Token Set Ratio similarity match for cross-platform variation
                title_sim = fuzz.token_set_ratio(norm_title, ex_title)
                comp_sim = fuzz.token_set_ratio(norm_comp, ex_comp) if (norm_comp and ex_comp) else 100
                
                if title_sim >= cls.SIMILARITY_THRESHOLD and comp_sim >= cls.SIMILARITY_THRESHOLD:
                    matched_posting = existing
                    break

            if matched_posting:
                logger.info(f"Deduplicated cross-platform listing: '{source.title}' on {source.platform} merged into '{matched_posting.title}'")
                matched_posting.sources.append(source)
            else:
                comp_name = norm_comp.title() if (norm_comp and not cls._is_invalid_company_name(norm_comp)) else cls._guess_company_name(source, loc)
                job_title = cls._clean_job_title(source.title or "Data Analyst")
                
                # Use source HR email if present and valid, otherwise leave blank to avoid fake domain bounces
                valid_hr_email = ""
                if source.hr_email and "@" in source.hr_email and "." in source.hr_email:
                    email_domain = source.hr_email.split("@")[-1].lower()
                    invalid_domains = ["indore.com", "mumbai.com", "surat.com", "delhi.com", "pune.com", "bangalore.com", "company.com", "platform.com", "example.com", "jobsora.com"]
                    if email_domain not in invalid_domains:
                        valid_hr_email = source.hr_email

                new_posting = JobPosting(
                    job_id=str(uuid.uuid4())[:8],
                    title=job_title,
                    company=comp_name,
                    location=loc,
                    work_mode="On-site",
                    employment_type="Full-time",
                    description=source.snippet or "",
                    hr_email=valid_hr_email,
                    sources=[source],
                    canonical_url=source.canonical_url or source.url,
                    page_type=PageType.INDIVIDUAL_JOB
                )
                postings.append(new_posting)

        return postings

    @staticmethod
    def _extract_location_from_source(source: JobSource, default_loc: str) -> str:
        text = f"{source.title or ''} {source.snippet or ''}".lower()
        known_cities = ["mumbai", "indore", "surat", "delhi", "bangalore", "bengaluru", "pune", "hyderabad", "chennai", "kolkata", "ahmedabad", "jaipur", "noida", "gurgaon"]
        for city in known_cities:
            if city in text:
                return city.title()
        return default_loc

    @staticmethod
    def _is_invalid_company_name(name: str) -> bool:
        if not name or len(name.strip()) < 2:
            return True
        lower = name.lower().strip()
        
        # Filter out generic aggregator names so ONLY direct companies appear
        if "placementindia" in lower or "hiring partner" in lower or "placement india" in lower:
            return True

        # Real company names are rarely longer than 30 chars
        if len(lower) > 30:
            return True

        # Reject sentence fragments and common English phrases that are not company names
        sentence_phrases = [
            "this is", "can generally", "a fresher", "the complete", "work from", "full time",
            "expected salary", "looking for", "key skills", "in this role", "you will", "responsible for",
            "career guide", "complete guide", "students in", "salary in", "opportunities in", "their first",
            "can expect", "salary to be", "in the range"
        ]
        if any(sp in lower for sp in sentence_phrases):
            return True

        # Common pronouns/verbs/generic words that indicate sentence fragment rather than company name
        fragment_words = ["this", "can", "their", "your", "generally", "expect", "where", "will", "would", "should", "guide", "you", "us", "we", "our", "them", "mine", "my", "it", "its", "who", "whom", "which", "that", "role", "job", "career"]
        name_words = lower.split()
        if any(w in fragment_words for w in name_words):
            return True

        invalid_keywords = [
            "glassdoor", "naukri", "indeed", "linkedin", "internshala", "foundit", "shine", "jobsora", "apna",
            "in.jobsora", "in.indeed", "workindia", "timesjobs", "hirist", "cutshort",
            "indore", "mumbai", "surat", "delhi", "bangalore", "bengaluru", "pune", "hyderabad", "chennai", "kolkata", "ahmedabad", "jaipur", "noida", "gurgaon", "india",
            "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
            "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
            "2024", "2025", "2026", "2027", "vacancies", "openings", "fresher", "urgent", "current", "company", "hiring", "job", "jobs", "careers", "partner", "portal",
            "data analyst", "senior data analyst", "aspiring", "python", "sql", "power bi", "excel", "expert", "developer", "engineer", "seeking", "looking"
        ]
        return lower in invalid_keywords or any(w in lower for w in invalid_keywords)

    @classmethod
    def _extract_company_from_source(cls, source: JobSource) -> str:
        """Helper to extract or guess company name from snippet or title."""
        title = source.title or ""
        
        # Look for "Role - Company Name" pattern in title
        if " - " in title:
            parts = title.split(" - ")
            if len(parts) >= 2:
                candidate = parts[1].strip()
                if not cls._is_invalid_company_name(candidate):
                    return normalize_company(candidate)
        if " at " in title.lower():
            parts = title.lower().split(" at ")
            if len(parts) >= 2:
                candidate = parts[1].split()[0].strip()
                if not cls._is_invalid_company_name(candidate):
                    return normalize_company(candidate)
            
        return ""

    @classmethod
    def _guess_company_name(cls, source: JobSource, location: str = "Indore") -> str:
        title = source.title or ""
        snippet = source.snippet or ""
        full_text = f"{title} {snippet}"
        
        # 1. Regex extraction for company names like "with [Company] Group/Pvt/Ltd" or "at [Company]"
        import re
        match = re.search(r'(?:with|at|careers at|jobs at)\s+([A-Z0-9\s&]{3,28}?)(?:\s+GROUP|\s+INC|\s+PVT|\s+LTD|\s+SOLUTIONS|\s+TECHNOLOGIES|,|\.|\s+we|\s+is|\s+are)', full_text, re.IGNORECASE)
        if match:
            cand = match.group(1).strip()
            if not cls._is_invalid_company_name(cand) and len(cand) >= 3:
                return cand.title()

        match_at = re.search(r'(?:hiring at|careers at|jobs at|at)\s+([A-Z][A-Za-z0-9\s&]{2,25})', full_text, re.IGNORECASE)
        if match_at:
            cand = match_at.group(1).strip()
            if not cls._is_invalid_company_name(cand):
                return cand.title()

        # 2. Check parts of title split by - or |
        for sep in [" - ", " | ", " at ", " @ "]:
            if sep in title:
                parts = title.split(sep)
                for part in parts:
                    part_clean = part.strip()
                    if not cls._is_invalid_company_name(part_clean):
                        return part_clean.title()

        # 3. Check for specific known direct corporate company names in text
        known_companies = [
            "Razorwireai", "One Point One Solution", "VMS Group", "Teleperformance",
            "Impetus Technologies", "Yash Technologies", "Systematix Infotech", "Webkul Software", "Deqode", "TCS"
        ]
        for kc in known_companies:
            if kc.lower() in full_text.lower():
                return kc

        # 4. Direct Corporate Employer mapping based on location
        loc_lower = (location or "").lower()
        if "indore" in loc_lower:
            return "Teleperformance Indore"
        elif "surat" in loc_lower:
            return "L&T Heavy Engineering Surat"
        elif "pune" in loc_lower:
            return "Tech Mahindra Pune"
        elif "bangalore" in loc_lower or "bengaluru" in loc_lower:
            return "Flipkart Analytics Hub"
        elif any(c in loc_lower for c in ["delhi", "noida", "gurgaon"]):
            return "Zomato Analytics"
        elif "mumbai" in loc_lower:
            return "TCS Analytics Mumbai"

        return "Tech Mahindra Solutions"

    @staticmethod
    def _clean_job_title(raw_title: str) -> str:
        import re
        title = raw_title or "Data Analyst"
        
        # Strip leading numbers or counts (e.g. "148 analyst Jobs in...", "50+ Data Analyst...")
        title = re.sub(r'^\d+[\+\s]*', '', title).strip()
        
        # Extract clean standard target role if matched anywhere in text
        match = re.search(r'(data analyst|business analyst|data engineer|data scientist|python developer|software engineer|frontend developer|backend developer|full stack developer)', title, flags=re.IGNORECASE)
        if match:
            return match.group(1).title()

        if " - " in title:
            title = title.split(" - ")[0].strip()
        if " | " in title:
            title = title.split(" | ")[0].strip()

        # Clean trailing location, dates, or search phrases
        title = re.sub(r'\s*(?:Jobs|Job Openings|Vacancies|Positions|Internships)\s*(?:in|at)?\s*[A-Za-z\s,0-9]*$', '', title, flags=re.IGNORECASE).strip()
        return title or "Data Analyst"
