"""
scraper_greenhouse.py — Greenhouse ATS scraper
URL: https://boards-api.greenhouse.io/v1/boards/{company}/jobs

Reliability: ⭐⭐⭐⭐⭐ (MOST RELIABLE — uses official public API, no scraping needed)

WHY THIS IS SPECIAL:
Greenhouse has a public JSON API for every company using their ATS.
No HTML parsing, no blocks, very stable. This is your most reliable source.

HOW TO ADD MORE COMPANIES:
Find a company's Greenhouse board slug by visiting:
  https://boards.greenhouse.io/COMPANYNAME
The slug is the part after the last slash.

Example companies known to use Greenhouse in NL:
  - booking (Booking.com)
  - adyen
  - messagebird (now Bird)
  - mollie
  - catawiki
  - coolblue
  - takeaway (Just Eat Takeaway)

⚠️ MANUAL MAINTENANCE: Add company slugs to COMPANIES list below as you discover them.
"""

import os
from http_client import fetch, polite_delay
from db import job_record, save_jobs

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

# ── Add/remove companies here ─────────────────────────────────────────────────
# Find slugs at: https://boards.greenhouse.io/SLUG
COMPANIES = [
    "booking",
    "adyen",
    "mollie",
    "catawiki",
    "takeaway",
    "messagebird",
    "picnic",
    "vandebron",
    "channable",
    "sendcloud",
]


def scrape(max_jobs: int = None) -> list[dict]:
    max_jobs = max_jobs or int(os.getenv("MAX_JOBS_PER_SOURCE", 50))
    jobs = []

    for company_slug in COMPANIES:
        if len(jobs) >= max_jobs:
            break

        print(f"  🔍 Greenhouse: fetching '{company_slug}'...")

        try:
            url = GREENHOUSE_API.format(slug=company_slug)
            response = fetch(url)
            data = response.json()

            listings = data.get("jobs", [])
            print(f"     Found {len(listings)} jobs")

            for listing in listings:
                if len(jobs) >= max_jobs:
                    break

                # Filter for Netherlands jobs
                location = listing.get("location", {}).get("name", "")
                if not _is_netherlands(location):
                    continue

                job_url = listing.get("absolute_url", "")
                description = _get_job_description(company_slug, listing.get("id"))

                job = job_record(
                    title=listing.get("title", "Unknown"),
                    company=_slug_to_name(company_slug),
                    description=description,
                    location=location,
                    source_url=job_url,
                    date_posted=listing.get("updated_at", "")[:10],
                    source="greenhouse",
                )
                jobs.append(job)

            polite_delay(1.0, 2.0)

        except Exception as e:
            print(f"  ❌ Greenhouse error for '{company_slug}': {e}")

    print(f"  ✅ Greenhouse: collected {len(jobs)} jobs")
    return jobs


def _get_job_description(company_slug: str, job_id: int) -> str:
    """Fetch full job description from Greenhouse API."""
    try:
        polite_delay(0.5, 1.5)
        url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs/{job_id}"
        response = fetch(url)
        data = response.json()
        # Strip HTML tags from description
        from bs4 import BeautifulSoup
        html = data.get("content", "")
        return BeautifulSoup(html, "lxml").get_text(separator="\n", strip=True)[:3000]
    except Exception:
        return ""


def _is_netherlands(location: str) -> bool:
    """Check if a job location is in the Netherlands."""
    nl_keywords = ["netherlands", "nederland", "amsterdam", "rotterdam", "utrecht",
                   "eindhoven", "den haag", "the hague", "remote", "nl"]
    location_lower = location.lower()
    return any(kw in location_lower for kw in nl_keywords)


def _slug_to_name(slug: str) -> str:
    """Convert a slug like 'booking' to a display name 'Booking'."""
    names = {
        "booking": "Booking.com",
        "adyen": "Adyen",
        "mollie": "Mollie",
        "catawiki": "Catawiki",
        "takeaway": "Just Eat Takeaway",
        "messagebird": "Bird (MessageBird)",
        "picnic": "Picnic",
        "vandebron": "Vandebron",
        "channable": "Channable",
        "sendcloud": "Sendcloud",
    }
    return names.get(slug, slug.title())


if __name__ == "__main__":
    jobs = scrape(max_jobs=10)
    for j in jobs:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
    result = save_jobs(jobs)
    print(f"\nSaved: {result}")
