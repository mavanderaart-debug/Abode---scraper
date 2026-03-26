"""
scraper_werkzoeken.py — Werkzoeken.nl scraper
URL: https://www.werkzoeken.nl

Reliability: ⭐⭐⭐⭐ (good HTML structure, Dutch-focused)

HOW IT WORKS:
- Uses Werkzoeken's search with location=nederland
- Parses standard job card HTML
"""

import os
from bs4 import BeautifulSoup
from http_client import fetch, polite_delay
from db import job_record, save_jobs

BASE_URL = "https://www.werkzoeken.nl"
SEARCH_URL = f"{BASE_URL}/vacatures"

SEARCH_QUERIES = [
    "software developer",
    "marketing manager",
    "sales",
    "product manager",
    "data",
    "designer",
]


def scrape(max_jobs: int = None) -> list[dict]:
    max_jobs = max_jobs or int(os.getenv("MAX_JOBS_PER_SOURCE", 50))
    jobs = []

    for query in SEARCH_QUERIES:
        if len(jobs) >= max_jobs:
            break

        print(f"  🔍 Werkzoeken: searching '{query}'...")

        try:
            params = {
                "q": query,
                "l": "Nederland",
                "p": 1,
            }
            response = fetch(SEARCH_URL, params=params)
            soup = BeautifulSoup(response.text, "lxml")

            # ⚠️ MANUAL CHECK: inspect werkzoeken.nl to confirm these selectors
            cards = (
                soup.find_all("div", class_=lambda c: c and "job" in str(c).lower())
                or soup.find_all("li", class_=lambda c: c and "result" in str(c).lower())
                or soup.select("article.vacancy, div.vacancy-card")
            )

            print(f"     Found {len(cards)} listings")

            for card in cards:
                if len(jobs) >= max_jobs:
                    break
                try:
                    job = _parse_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    print(f"     ⚠️  Skipping: {e}")

        except Exception as e:
            print(f"  ❌ Werkzoeken error for '{query}': {e}")

    print(f"  ✅ Werkzoeken: collected {len(jobs)} jobs")
    return jobs


def _parse_card(card) -> dict | None:
    title_el = card.find(["h2", "h3", "h4"]) or card.find(class_=lambda c: c and "title" in str(c).lower())
    if not title_el:
        return None
    title = title_el.get_text(strip=True)
    if not title:
        return None

    company_el = card.find(class_=lambda c: c and "company" in str(c).lower() or "employer" in str(c).lower())
    company = company_el.get_text(strip=True) if company_el else "Unknown"

    location_el = card.find(class_=lambda c: c and "location" in str(c).lower() or "city" in str(c).lower())
    location = location_el.get_text(strip=True) if location_el else "Nederland"

    link_el = card.find("a", href=True)
    if not link_el:
        return None
    url = link_el["href"]
    if not url.startswith("http"):
        url = BASE_URL + url

    date_el = card.find("time") or card.find(class_=lambda c: c and "date" in str(c).lower())
    date_posted = date_el.get("datetime") if date_el else None

    description = _get_description(url)

    return job_record(
        title=title,
        company=company,
        description=description,
        location=location,
        source_url=url,
        date_posted=date_posted,
        source="werkzoeken",
    )


def _get_description(url: str) -> str:
    try:
        polite_delay(1.0, 2.5)
        response = fetch(url)
        soup = BeautifulSoup(response.text, "lxml")
        desc_el = (
            soup.find(class_=lambda c: c and "description" in str(c).lower())
            or soup.find("article")
            or soup.find("main")
        )
        return desc_el.get_text(separator="\n", strip=True)[:3000] if desc_el else ""
    except Exception:
        return ""


if __name__ == "__main__":
    jobs = scrape(max_jobs=5)
    for j in jobs:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
    result = save_jobs(jobs)
    print(f"\nSaved: {result}")
