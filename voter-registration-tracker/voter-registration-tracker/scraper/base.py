"""
scraper/base.py
Shared HTTP helpers: retries, PDF extraction, HTML parsing utils.
All state scrapers inherit from or use these.
"""

import io
import time
from datetime import date
from typing import Optional

import pdfplumber
import requests
from bs4 import BeautifulSoup

from config import REQUEST_HEADERS, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF


def fetch_html(url: str) -> BeautifulSoup:
    """Fetch a URL and return parsed BeautifulSoup. Retries on failure."""
    resp = _get_with_retry(url)
    return BeautifulSoup(resp.text, "html.parser")


def fetch_bytes(url: str) -> bytes:
    """Fetch a URL and return raw bytes (for CSV/PDF downloads)."""
    resp = _get_with_retry(url)
    return resp.content


def fetch_csv_text(url: str) -> str:
    """Fetch a URL and return text (for CSV parsing)."""
    resp = _get_with_retry(url)
    return resp.text


def fetch_pdf_text(url: str) -> str:
    """Fetch a PDF and return all extracted text, page by page."""
    content = fetch_bytes(url)
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages)


def fetch_pdf_tables(url: str) -> list[list[list[str]]]:
    """Fetch a PDF and return tables extracted from each page."""
    content = fetch_bytes(url)
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        tables = []
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables


def _get_with_retry(url: str) -> requests.Response:
    backoff = RETRY_BACKOFF
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                url,
                headers=REQUEST_HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(backoff)
                backoff *= 2
    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts: {last_exc}")


def parse_int(s: str) -> int:
    """Parse a formatted integer string like '1,234,567' → 1234567."""
    if s is None:
        return 0
    return int(str(s).replace(",", "").replace(" ", "").strip())


def parse_float(s: str) -> float:
    """Parse a percentage string like '34.5%' or '34.5' → 34.5."""
    if s is None:
        return 0.0
    return float(str(s).replace("%", "").replace(",", "").strip())


def safe_pct(part: int, total: int) -> float:
    """Compute percentage, handling zero total."""
    if total == 0:
        return 0.0
    return round(part / total * 100, 2)


def parse_month_year(s: str) -> Optional[date]:
    """
    Parse common date formats found on state websites.
    Returns a date set to the 1st of the month, or None.
    """
    import re
    from datetime import datetime

    s = s.strip()
    formats = [
        "%B %Y",    # April 2025
        "%b %Y",    # Apr 2025
        "%m/%Y",    # 04/2025
        "%Y-%m",    # 2025-04
        "%m/%d/%Y", # 04/01/2025
        "%B %d, %Y",# April 1, 2025
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date().replace(day=1)
        except ValueError:
            continue
    # Try regex for "as of Month Day, Year"
    m = re.search(r"(\w+ \d{1,2},?\s*\d{4})", s)
    if m:
        for fmt in ["%B %d, %Y", "%B %d %Y"]:
            try:
                return datetime.strptime(m.group(1), fmt).date().replace(day=1)
            except ValueError:
                continue
    return None
