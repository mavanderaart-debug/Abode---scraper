"""
scraper_lever.py — Lever ATS scraper
URL: https://api.lever.co/v0/postings/{company}

Reliability: ⭐⭐⭐⭐⭐ (MOST RELIABLE — uses official public API)

HOW TO FIND COMPANY SLUGS:
Visit: https://jobs.lever.co/COMPANYNAME
The slug is the part after the last slash.

Example Dutch companies on Lever:
  - netflix (has NL office)
  - uber
  - airbnb
  - miro
  - typeform
  - personio
  - contentful

⚠️ MANUAL MAINTENANCE: Add/remove slugs as needed.
"""

import os
from http_client import fetch, polite_delay
from db import job_record, save_jobs

LEVER_API = "https://api.lever.co/v0/postings/{slug}?mode=json"

# ── Add/remove companies here ─────────────────────────────────────────────────
COMPANIES = [
    "netflix",
    "uber",
    "miro",
    "typeform",
    "personio",
    "contentful",
    "elastic",
    "intercom",
    "figma",
    "notion",
]


def scrape(max_jobs: int = None) -> list[dict]:
    max_jobs = max_jobs or int(os.getenv("MAX_JOBS_PER_SOURCE", 50))
    jobs = []

    for company_slug in COMPANIES:
        if len(jobs) >= max_jobs:
            break

        print(f"  🔍 Lever: fetching '{company_slug}'...")

        try:
            url = LEVER_API.format(slug=company_slug)
            response = fetch(url)
            listings = response.json()

            if not isinstance(listings, list):
                continue

            # Filter NL jobs
            nl_listings = [l for l in listings if _is_netherlands(
                l.get("categories", {}).get("location", "") + " " +
                l.get("text", "")
            )]

            print(f"     Found {len(nl_listings)} NL jobs (of {len(listings)} total)")

            for listing in nl_listings:
                if len(jobs) >= max_jobs:
                    break

                location = listing.get("categories", {}).get("location", "Netherlands")
                description = _extract_description(listing)
                job_url = listing.get("hostedUrl", "")

                job = job_record(
                    title=listing.get("text", "Unknown"),
                    company=_slug_to_name(company_slug),
                    description=description,
                    location=location,
                    source_url=job_url,
                    date_posted=None,
                    source="lever",
                )
                jobs.append(job)

            polite_delay(1.0, 2.0)

        except Exception as e:
            print(f"  ❌ Lever error for '{company_slug}': {e}")

    print(f"  ✅ Lever: collected {len(jobs)} jobs")
    return jobs


def _extract_description(listing: dict) -> str:
    """Extract and clean job description from Lever JSON."""
    from bs4 import BeautifulSoup
    parts = []
    for section in listing.get("descriptionPlain", "").split("\n"):
        parts.append(section)
    lists = listing.get("lists", [])
    for lst in lists:
        parts.append(lst.get("text", ""))
        parts.append(lst.get("content", ""))
    return "\n".join(parts)[:3000]


def _is_netherlands(text: str) -> bool:
    nl_keywords = ["netherlands", "nederland", "amsterdam", "rotterdam", "utrecht",
                   "eindhoven", "den haag", "the hague", "nl,", "nl "]
    return any(kw in text.lower() for kw in nl_keywords)


def _slug_to_name(slug: str) -> str:
    names = {
        "netflix": "Netflix",
        "uber": "Uber",
        "miro": "Miro",
        "typeform": "Typeform",
        "personio": "Personio",
        "contentful": "Contentful",
        "elastic": "Elastic",
        "intercom": "Intercom",
        "figma": "Figma",
        "notion": "Notion",
    }
    return names.get(slug, slug.title())


if __name__ == "__main__":
    jobs = scrape(max_jobs=10)
    for j in jobs:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
    result = save_jobs(jobs)
    print(f"\nSaved: {result}")
