import re
import unicodedata
from typing import List

def clean_text(text: str) -> str:
    """Clean and normalize raw extracted text from PDF/web pages."""
    if not text:
        return ""
    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)
    # Remove null bytes & non-printable ASCII except standard whitespace
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # Standardize newline characters
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Collapse multiple blank lines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Collapse spaces per line
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(lines).strip()

clean_resume_text = clean_text

def normalize_title(title: str) -> str:
    """Normalize job title for comparison and matching."""
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r'[^a-z0-9\s#\+]', ' ', title)
    return ' '.join(title.split())

def normalize_company(company: str) -> str:
    """Normalize company name for deduplication."""
    if not company:
        return ""
    comp = company.lower()
    suffixes = [r'\bpvt\b', r'\bltd\b', r'\binc\b', r'\bcorp\b', r'\bllc\b', r'\blimited\b', r'\btechnologies\b', r'\bsolutions\b', r'\bservices\b', r'\bprivate\b']
    for suffix in suffixes:
        comp = re.sub(suffix, '', comp)
    comp = re.sub(r'[^a-z0-9\s]', '', comp)
    return ' '.join(comp.split())

def extract_keywords(text: str) -> List[str]:
    """Extract key technical and domain keywords from text."""
    if not text:
        return []
    words = re.findall(r'\b[A-Za-z0-9\+\#\.]{2,}\b', text)
    stopwords = {
        'and', 'the', 'for', 'with', 'you', 'will', 'are', 'this', 'that', 'have',
        'from', 'your', 'about', 'more', 'their', 'work', 'team', 'data', 'using'
    }
    keywords = sorted(list(set(w.lower() for w in words if w.lower() not in stopwords)))
    return keywords
