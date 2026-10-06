from typing import List, Tuple
from app.models.job import JobSource, PageType
from app.utils.urls import clean_url, classify_url_type
from app.utils.logging import logger

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

class URLValidator:
    @staticmethod
    def validate_and_classify_sources(sources: List[JobSource]) -> Tuple[List[JobSource], List[JobSource]]:
        """
        Validate URLs and classify into Individual Jobs vs Listing Pages / Invalid URLs.
        Returns (individual_jobs, listing_and_invalid_pages)
        """
        individual_jobs = []
        rejected_sources = []

        for source in sources:
            cleaned = clean_url(source.url)
            if not cleaned:
                source.canonical_url = ""
                rejected_sources.append(source)
                continue
                
            source.canonical_url = cleaned
            title_lower = (source.title or "").lower()
            
            # Reject social media pages, youtube videos, non-job career guide articles, blogs, course advertisements, and generic search aggregators
            url_lower = cleaned.lower()
            non_job_keywords = ["course", "youtube", "how to become", "training", "tutorial", "salary report", "career guide", "complete guide", "roadmap", "career options", "interview questions", "what is", "salary of a"]
            blog_url_paths = ["/blog/", "/blogs/", "/article/", "/articles/", "/post/", "/posts/", "/guide/", "/guides/", "/tutorial/"]
            if any(w in title_lower for w in non_job_keywords) or \
               any(p in url_lower for p in blog_url_paths) or \
               any(s in url_lower for s in ["instagram.com", "youtube.com", "youtu.be", "facebook.com", "twitter.com", "x.com", "pinterest.com"]):
                logger.info(f"Rejected non-job content/article/blog/social source: {source.title} - {cleaned}")
                rejected_sources.append(source)
                continue

            page_type_str = classify_url_type(cleaned, source.title or "", source.snippet or "")
            
            # Allow INDIVIDUAL_JOB and clean job sources (rejecting generic search aggregators and course pages)
            if page_type_str in ["INDIVIDUAL_JOB", "COMPANY_PAGE", "UNKNOWN"]:
                individual_jobs.append(source)
            elif page_type_str in ["LISTING_PAGE", "SEARCH_PAGE"]:
                # If listing page title contains clear role and specific employer, allow but clean title/company
                if "hiring" in title_lower or "analyst" in title_lower or "developer" in title_lower:
                    individual_jobs.append(source)
                else:
                    logger.info(f"Rejected generic search listing page: {source.title} - {cleaned}")
                    rejected_sources.append(source)
            else:
                logger.info(f"Source classified as {page_type_str} (invalid URL): {source.title} - {cleaned}")
                rejected_sources.append(source)

        return individual_jobs, rejected_sources

URLClassifierService = URLValidator
normalize_canonical_url = clean_url
