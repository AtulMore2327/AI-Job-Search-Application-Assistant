"""
Full Job Description (JD) Extraction Service.
Extracts clean, readable job description body text from accessible HTML pages using multi-signal parsing
(Schema.org JobPosting, semantic containers, and text cleaning) with text-size protection limits.
"""

import re
import json
from typing import Optional, List, Union, Any, Tuple
import httpx
from bs4 import BeautifulSoup

from app.models.job import Job, JDExtractResult
from app.services.metadata_extractor import generate_stable_job_id
from app.services.url_validator import DEFAULT_USER_AGENT, normalize_canonical_url
from app.utils.text import clean_text
from app.utils.logging import get_logger

logger = get_logger("jd_extractor")

# Maximum text size allowed to protect prompt token limits (approx 15,000 characters)
MAX_JD_CHAR_LIMIT = 15000

# CSS selectors commonly containing primary job description content
JD_CONTAINER_SELECTORS = [
    "[itemprop='description']",
    "#job-description",
    ".job-description",
    ".description",
    ".show-more-less-html",
    ".job-details",
    ".vacancy-description",
    ".details-section",
    ".job-desc",
    ".posting-requirements",
    "main",
    "article"
]


def clean_jd_text(text: str, max_chars: int = MAX_JD_CHAR_LIMIT) -> Tuple[str, bool]:
    """
    Clean raw job description text.
    Strips noise, cookie banners, excessive whitespace, and truncates if exceeding max_chars.
    
    Returns:
        Tuple of (cleaned_text, is_truncated)
    """
    if not text:
        return ("", False)
        
    # Remove null bytes and unprintable characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    text = text.replace('\xa0', ' ').replace('\u200b', '')
    
    # Strip cookie banner noise patterns
    noise_patterns = [
        r'accept\s+all\s+cookies.*',
        r'we\s+use\s+cookies\s+to\s+improve.*',
        r'share\s+this\s+job:\s*facebook\s*twitter.*'
    ]
    for p in noise_patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
        
    # Normalize empty lines
    lines = [line.strip() for line in text.splitlines()]
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned_lines.append("")
                prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False
            
    full_cleaned = "\n".join(cleaned_lines).strip()
    
    # Text-size protection: truncate if exceeding max_chars limit
    if len(full_cleaned) > max_chars:
        truncated_text = full_cleaned[:max_chars].rsplit(" ", 1)[0] + "\n[Text truncated due to maximum size limits...]"
        return (truncated_text, True)
        
    return (full_cleaned, False)


class FullJDExtractor:
    """Service to fetch accessible HTML and extract readable Job Description text."""
    
    def __init__(self, timeout: float = 5.0, max_chars: int = MAX_JD_CHAR_LIMIT):
        self.timeout = timeout
        self.max_chars = max_chars

    def extract_jd_from_html(
        self,
        html_content: str,
        url: str,
        job_id: Optional[str] = None
    ) -> JDExtractResult:
        """
        Extract clean JD text from HTML string.
        """
        canonical = normalize_canonical_url(url)
        jid = job_id or generate_stable_job_id("Unknown", "Unknown", "Unknown", canonical)
        
        if not html_content or not html_content.strip():
            return JDExtractResult(
                job_id=jid,
                url=canonical,
                accessible=True,
                raw_jd_text="",
                text_length=0,
                truncated=False,
                error="HTML content is empty."
            )

        soup = BeautifulSoup(html_content, "html.parser")
        
        raw_jd_body = ""
        
        # Signal 1: Schema.org JobPosting description (parsed before script tags are decomposed)
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, dict) and item.get("@type", "").lower() == "jobposting":
                            desc = item.get("description", "")
                            if desc:
                                desc_soup = BeautifulSoup(desc, "html.parser")
                                raw_jd_body = desc_soup.get_text(separator="\n")
                                break
                except Exception:
                    pass
            if raw_jd_body:
                break

        # Strip irrelevant non-content elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe"]):
            element.decompose()

        # Signal 2: Semantic JD Containers
        if not raw_jd_body:
            for selector in JD_CONTAINER_SELECTORS:
                container = soup.select_one(selector)
                if container:
                    raw_jd_body = container.get_text(separator="\n")
                    if len(raw_jd_body.strip()) > 100:
                        break

        # Signal 3: Body fallback
        if not raw_jd_body and soup.body:
            raw_jd_body = soup.body.get_text(separator="\n")

        cleaned_text, is_truncated = clean_jd_text(raw_jd_body, max_chars=self.max_chars)
        
        return JDExtractResult(
            job_id=jid,
            url=canonical,
            accessible=True,
            raw_jd_text=cleaned_text,
            text_length=len(cleaned_text),
            truncated=is_truncated,
            error=None if cleaned_text else "No readable job description content found."
        )

    def extract_jd_from_url(
        self,
        url: str,
        job_id: Optional[str] = None,
        mock_client: Optional[Any] = None
    ) -> JDExtractResult:
        """
        Fetch HTML from URL and extract full JD text. Handles HTTP failures without crashing.
        """
        canonical = normalize_canonical_url(url)
        jid = job_id or generate_stable_job_id("Unknown", "Unknown", "Unknown", canonical)

        try:
            client = mock_client or httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": DEFAULT_USER_AGENT}
            )
            
            response = client.get(canonical)
            if response.status_code >= 400:
                logger.warning(f"HTTP Error {response.status_code} fetching URL: {canonical}")
                return JDExtractResult(
                    job_id=jid,
                    url=canonical,
                    accessible=False,
                    raw_jd_text="",
                    text_length=0,
                    truncated=False,
                    error=f"HTTP Error {response.status_code}"
                )
                
            return self.extract_jd_from_html(response.text, canonical, job_id=jid)

        except Exception as e:
            logger.error(f"Error fetching URL '{canonical}' for JD extraction: {e}")
            return JDExtractResult(
                job_id=jid,
                url=canonical,
                accessible=False,
                raw_jd_text="",
                text_length=0,
                truncated=False,
                error=f"HTTP request failed: {str(e)}"
            )

    def extract_jd_batch(
        self,
        items: List[Union[str, Job]],
        mock_client: Optional[Any] = None
    ) -> List[JDExtractResult]:
        """
        Batch extract full JD text for multiple URLs or Job objects with single item failure isolation.
        """
        results: List[JDExtractResult] = []
        for item in items:
            try:
                if isinstance(item, Job):
                    res = self.extract_jd_from_url(item.canonical_url, job_id=item.job_id, mock_client=mock_client)
                else:
                    res = self.extract_jd_from_url(str(item), mock_client=mock_client)
                results.append(res)
            except Exception as e:
                url_str = item.canonical_url if isinstance(item, Job) else str(item)
                jid = item.job_id if isinstance(item, Job) else generate_stable_job_id("Unknown", "Unknown", "Unknown", url_str)
                logger.error(f"Batch JD extraction error for '{url_str}': {e}")
                results.append(JDExtractResult(
                    job_id=jid,
                    url=url_str,
                    accessible=False,
                    raw_jd_text="",
                    text_length=0,
                    truncated=False,
                    error=str(e)
                ))
        return results
