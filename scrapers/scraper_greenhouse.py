"""
scraper_greenhouse.py — Greenhouse ATS scraper
URL: https://boards-api.greenhouse.io/v1/boards/{company}/jobs

Reliability: ⭐⭐⭐⭐⭐ (MOST RELIABLE — uses official public API, no scraping needed)

HOW TO ADD MORE COMPANIES:
Find a company's Greenhouse board slug by visiting:
  https://boards.greenhouse.io/COMPANYNAME
  The slug is the part after the last slash.
  """

import os
from http_client import fetch, polite_delay
from db import job_record, save_jobs

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

# ── Verified Dutch & NL-hiring companies on Greenhouse ───────────────────────
COMPANIES = [
      # Dutch tech scale-ups
    ("adyen",           "Adyen"),
      ("mollie",          "Mollie"),
      ("catawiki",        "Catawiki"),
      ("sendcloud",       "Sendcloud"),
      ("picnic",          "Picnic"),
      ("channable",       "Channable"),
      ("vandebron",       "Vandebron"),
      ("messagebird",     "Bird (MessageBird)"),
      ("takeaway",        "Just Eat Takeaway"),
      ("coolblue",        "Coolblue"),
      # International companies with NL offices
      ("uber",            "Uber"),
      ("booking",         "Booking.com"),
      ("TomTom",          "TomTom"),
      ("elastic",         "Elastic"),
      ("aiven",           "Aiven"),
      ("immutable",       "Immutable"),
      ("lightspeedhq",    "Lightspeed"),
      ("miro",            "Miro"),
      ("polarsteps",      "Polarsteps"),
      ("payu",            "PayU"),
      ("usabilla",        "Usabilla"),
      ("backbase",        "Backbase"),
      ("ohpen",           "Ohpen"),
      ("nmbrs",           "Nmbrs"),
      ("temper",          "Temper"),
      ("werkspoorbouw",   "Werkspoor"),
      ("randstad",        "Randstad"),
      ("pggm",            "PGGM"),
      ("ing",             "ING"),
      ("abnamro",         "ABN AMRO"),
]


def scrape(max_jobs: int = None) -> list[dict]:
      max_jobs = max_jobs or int(os.getenv("MAX_JOBS_PER_SOURCE", 50))
      jobs = []

    for company_slug, company_name in COMPANIES:
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

                              location = listing.get("location", {}).get("name", "")
                              if not _is_netherlands(location):
                                                    continue

                              job_url = listing.get("absolute_url", "")
                              description = _get_job_description(company_slug, listing.get("id"))

                job = job_record(
                                      title=listing.get("title", "Unknown"),
                                      company=company_name,
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
      try:
                polite_delay(0.5, 1.5)
                url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs/{job_id}"
                response = fetch(url)
                data = response.json()
                from bs4 import BeautifulSoup
                html = data.get("content", "")
                return BeautifulSoup(html, "lxml").get_text(separator="\n", strip=True)[:3000]
except Exception:
        return ""


def _is_netherlands(location: str) -> bool:
      nl_keywords = ["netherlands", "nederland", "amsterdam", "rotterdam", "utrecht",
                                        "eindhoven", "den haag", "the hague", "remote", "nl"]
      location_lower = location.lower()
      return any(kw in location_lower for kw in nl_keywords)


if __name__ == "__main__":
      jobs = scrape(max_jobs=10)
      for j in jobs:
                print(f"  {j['title']} @ {j['company']} — {j['location']}")
            result = save_jobs(jobs)
    print(f"\nSaved: {result}")
