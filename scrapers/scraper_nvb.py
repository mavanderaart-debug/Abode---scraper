"""
scraper_nvb.py — Nationale Vacaturebank scraper
URL: https://www.nationalevacaturebank.nl

Reliability: ⭐⭐⭐⭐⭐ (most reliable, clean HTML, Dutch-focused)
This is your best starting source for Netherlands jobs.

HOW IT WORKS:
- Searches for jobs via their public search page
- Parses job listings from HTML
- Follows each job link to get the full description
"""

import os
from bs4 import BeautifulSoup
from http_client import fetch, polite_delay
from db import job_record, save_jobs

BASE_URL = "https://www.nationalevacaturebank.nl"
SEARCH_URL = f"{BASE_URL}/vacature/zoeken"

# ── Adjust these search terms to match your target roles ──────────────────────
SEARCH_QUERIES = [
    "software engineer",
    "product manager",
    "marketing",
    "sales",
    "data analyst",
    "designer",
]


def scrape(max_jobs: int = None) -> list[dict]:
    max_jobs = max_jobs or int(os.getenv("MAX_JOBS_PER_SOURCE", 50))
    jobs = []

    for query in SEARCH_QUERIES:
        if len(jobs) >= max_jobs:
            break

        print(f"  🔍 NVB: searching '{query}'...")

        try:
            params = {
                "query": query,
                "location": "Nederland",
                "distance": "50",
                "page": "1",
            }
            response = fetch(SEARCH_URL, params=params)
            soup = BeautifulSoup(response.text, "lxml")

            # Find job cards — NVB uses article tags with class 'vacancy-card'
            # ⚠️ MANUAL CHECK: if this stops working, inspect the page in your browser
            # and look for the HTML element that wraps each job listing
            cards = soup.find_all("article", class_=lambda c: c and "vacancy" in c.lower())

            if not cards:
                # Fallback: try generic list items
                cards = soup.select("li.search-result, div.vacancy-item, div[data-job-id]")

            print(f"     Found {len(cards)} listings")

            for card in cards:
                if len(jobs) >= max_jobs:
                    break
                try:
                    job = _parse_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    print(f"     ⚠️  Skipping card: {e}")

        except Exception as e:
            print(f"  ❌ NVB error for '{query}': {e}")

    print(f"  ✅ NVB: collected {len(jobs)} jobs")
    return jobs


def _parse_card(card) -> dict | None:
    """Extract job data from a single NVB listing card."""

    # Title
    title_el = card.find(["h2", "h3", "h4"]) or card.find(class_=lambda c: c and "title" in str(c).lower())
    if not title_el:
        return None
    title = title_el.get_text(strip=True)

    # Company
    company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
    company = company_el.get_text(strip=True) if company_el else "Unknown"

    # Location
    location_el = card.find(class_=lambda c: c and "location" in str(c).lower())
    location = location_el.get_text(strip=True) if location_el else "Nederland"

    # URL
    link_el = card.find("a", href=True)
    if not link_el:
        return None
    url = link_el["href"]
    if not url.startswith("http"):
        url = BASE_URL + url

    # Date
    date_el = card.find("time") or card.find(class_=lambda c: c and "date" in str(c).lower())
    date_posted = date_el.get("datetime") or (date_el.get_text(strip=True) if date_el else None)

    # Get full description from detail page
    description = _get_description(url)

    return job_record(
        title=title,
        company=company,
        description=description,
        location=location,
        source_url=url,
        date_posted=date_posted,
        source="nationalevacaturebank",
    )


def _get_description(url: str) -> str:
    """Fetch the job detail page and extract the description."""
    try:
        polite_delay(1.0, 2.5)
        response = fetch(url)
        soup = BeautifulSoup(response.text, "lxml")

        # Look for the main job description container
        desc_el = (
            soup.find(class_=lambda c: c and "description" in str(c).lower())
            or soup.find(class_=lambda c: c and "vacancy-body" in str(c).lower())
            or soup.find("article")
            or soup.find("main")
        )
        return desc_el.get_text(separator="\n", strip=True)[:3000] if desc_el else ""
    except Exception:
        return ""


if __name__ == "__main__":
    # Test this scraper individually: python scrapers/scraper_nvb.py
    jobs = scrape(max_jobs=5)
    for j in jobs:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
    result = save_jobs(jobs)
    print(f"\nSaved: {result}")
