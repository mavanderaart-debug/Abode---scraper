"""
scraper_ashby.py — Ashby ATS scraper
URL: https://api.ashbyhq.com/posting-api/job-board/{company}

Reliability: ⭐⭐⭐⭐⭐ (MOST RELIABLE — official public API)

Ashby is increasingly popular with tech startups.
Many Dutch scale-ups and international companies use it.

HOW TO FIND SLUGS:
Visit: https://jobs.ashbyhq.com/COMPANYNAME
The slug is the COMPANYNAME part.

⚠️ MANUAL MAINTENANCE: Add slugs as you discover companies using Ashby.
"""

import os
from http_client import fetch, polite_delay
from db import job_record, save_jobs

ASHBY_API = "https://api.ashbyhq.com/posting-api/job-board/{slug}"

# ── Add/remove companies here ─────────────────────────────────────────────────
COMPANIES = [
    "monzo",
    "revolut",
    "wise",
    "deliveroo",
    "gorillas",
    "getir",
    "bynder",
    "lightspeed",
    "payhawk",
    "remote",
]


def scrape(max_jobs: int = None) -> list[dict]:
    max_jobs = max_jobs or int(os.getenv("MAX_JOBS_PER_SOURCE", 50))
    jobs = []

    for company_slug in COMPANIES:
        if len(jobs) >= max_jobs:
            break

        print(f"  🔍 Ashby: fetching '{company_slug}'...")

        try:
            url = ASHBY_API.format(slug=company_slug)
            response = fetch(url)
            data = response.json()

            listings = data.get("jobs", [])
            print(f"     Found {len(listings)} total jobs")

            for listing in listings:
                if len(jobs) >= max_jobs:
                    break

                location = listing.get("location", "")
                if not _is_netherlands(location):
                    continue

                # Build URL
                job_url = f"https://jobs.ashbyhq.com/{company_slug}/{listing.get('id', '')}"

                description = _extract_description(listing)

                job = job_record(
                    title=listing.get("title", "Unknown"),
                    company=_slug_to_name(company_slug),
                    description=description,
                    location=location,
                    source_url=job_url,
                    date_posted=listing.get("publishedDate", "")[:10] if listing.get("publishedDate") else None,
                    source="ashby",
                )
                jobs.append(job)

            polite_delay(1.0, 2.0)

        except Exception as e:
            print(f"  ❌ Ashby error for '{company_slug}': {e}")

    print(f"  ✅ Ashby: collected {len(jobs)} jobs")
    return jobs


def _extract_description(listing: dict) -> str:
    from bs4 import BeautifulSoup
    html = listing.get("descriptionHtml", "") or listing.get("description", "")
    if html:
        return BeautifulSoup(html, "lxml").get_text(separator="\n", strip=True)[:3000]
    return listing.get("descriptionPlain", "")[:3000]


def _is_netherlands(location: str) -> bool:
    nl_keywords = ["netherlands", "nederland", "amsterdam", "rotterdam", "utrecht",
                   "eindhoven", "den haag", "the hague", "remote", "nl"]
    return any(kw in location.lower() for kw in nl_keywords)


def _slug_to_name(slug: str) -> str:
    names = {
        "monzo": "Monzo",
        "revolut": "Revolut",
        "wise": "Wise",
        "deliveroo": "Deliveroo",
        "gorillas": "Gorillas",
        "getir": "Getir",
        "bynder": "Bynder",
        "lightspeed": "Lightspeed",
        "payhawk": "Payhawk",
        "remote": "Remote.com",
    }
    return names.get(slug, slug.title())


if __name__ == "__main__":
    jobs = scrape(max_jobs=10)
    for j in jobs:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
    result = save_jobs(jobs)
    print(f"\nSaved: {result}")
