"""Job Description Ingestion & Web Scraping Module.

Fetches job postings from URLs or parses raw text inputs.
Sanitizes page layout elements and extracts job description bodies.
"""

from typing import Dict
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from app.config import USER_AGENT
from app.parsers.text_cleaner import clean_text


class ScrapingError(Exception):
    """Raised when web scraping a job posting fails."""
    pass


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid HTTP/HTTPS URL."""
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def scrape_job_description_url(url: str, timeout_sec: float = 12.0) -> Dict[str, str]:
    """Scrape and extract clean job description prose from a web URL.

    Args:
        url: The web page URL of the job posting.
        timeout_sec: Maximum HTTP request wait time.

    Returns:
        Dict with 'title', 'url', and 'text'.
    """
    url = url.strip()
    if not is_valid_url(url):
        raise ScrapingError(f"Invalid URL format: '{url}'. Must start with http:// or https://")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        with httpx.Client(follow_redirects=True, timeout=timeout_sec, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
            html_content = response.text
    except httpx.HTTPStatusError as e:
        raise ScrapingError(f"HTTP error {e.response.status_code} when fetching job posting from {url}") from e
    except httpx.RequestError as e:
        raise ScrapingError(f"Network error accessing job posting: {str(e)}") from e
    except Exception as e:
        raise ScrapingError(f"Unexpected error fetching job posting: {str(e)}") from e

    soup = BeautifulSoup(html_content, "html.parser")

    # Extract page title
    page_title = ""
    if soup.title and soup.title.string:
        page_title = soup.title.string.strip()

    # Strip non-content tags
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "button", "form", "aside"]):
        tag.decompose()

    # Search for job-description-specific containers
    candidate_selectors = [
        '[data-testid="job-description"]',
        '[class*="job-description"]',
        '[class*="jobDescription"]',
        '[id*="job-description"]',
        '[id*="jobDescription"]',
        'article',
        'main',
        '.content',
        '#content'
    ]

    selected_container = None
    for selector in candidate_selectors:
        found = soup.select_one(selector)
        if found and len(found.get_text(strip=True)) > 200:
            selected_container = found
            break

    target_element = selected_container if selected_container else (soup.body or soup)
    extracted_text = target_element.get_text(separator="\n")
    cleaned_jd = clean_text(extracted_text)

    if len(cleaned_jd) < 50:
        raise ScrapingError(
            "Could not extract sufficient job description text from this URL. "
            "The site might require JavaScript rendering or login. Please paste the job description text directly."
        )

    return {
        "title": page_title or "Job Posting",
        "url": url,
        "text": cleaned_jd
    }
