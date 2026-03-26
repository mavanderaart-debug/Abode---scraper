"""
http_client.py — Shared HTTP helper.
Handles headers, retries, and rate limiting for all scrapers.
"""

import time
import random
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

# Rotate through realistic browser headers to avoid blocks
HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "nl-NL,nl;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    },
]


def get_headers() -> dict:
    """Return a random set of browser-like headers."""
    return random.choice(HEADERS_LIST)


def polite_delay(min_s: float = 1.5, max_s: float = 4.0):
    """Wait a random amount of time between requests. Be polite to servers."""
    time.sleep(random.uniform(min_s, max_s))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch(url: str, params: dict = None, timeout: int = 15) -> httpx.Response:
    """
    Fetch a URL with retries, rotating headers, and polite delays.
    Raises an exception if the request fails after 3 attempts.
    """
    polite_delay()
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        response = client.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        return response
