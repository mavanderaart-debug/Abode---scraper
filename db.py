"""
db.py — Supabase connection and job saving logic.
All scrapers use this to save jobs consistently.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def save_jobs(jobs: list[dict]) -> dict:
    """
    Save a list of jobs to Supabase.
    Skips duplicates based on source_url.
    Returns a summary: {"saved": N, "skipped": N, "errors": N}
    """
    if not jobs:
        return {"saved": 0, "skipped": 0, "errors": 0}

    client = get_client()
    saved = skipped = errors = 0

    for job in jobs:
        try:
            # Check for duplicate by source_url
            existing = (
                client.table("jobs")
                .select("id")
                .eq("source_url", job["source_url"])
                .execute()
            )

            if existing.data:
                skipped += 1
                continue

            # Insert new job
            client.table("jobs").insert(job).execute()
            saved += 1

        except Exception as e:
            print(f"  ⚠️  Error saving job '{job.get('title', '?')}': {e}")
            errors += 1

    return {"saved": saved, "skipped": skipped, "errors": errors}


def job_record(
    title: str,
    company: str,
    description: str,
    location: str,
    source_url: str,
    date_posted: str | None = None,
    work_mode: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    salary_currency: str = "EUR",
    source: str = "unknown",
) -> dict:
    """
    Helper to build a consistently structured job dict.
    Use this in every scraper so fields are always the same.
    """
    return {
        "title": title.strip(),
        "company": company.strip(),
        "description": description.strip(),
        "location": location.strip(),
        "source_url": source_url.strip(),
        "date_posted": date_posted,
        "work_mode": work_mode,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": salary_currency,
        "source": source,
        "is_active": True,
    }
