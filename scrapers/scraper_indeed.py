"""
scraper_indeed.py — Indeed Netherlands scraper
URL: https://nl.indeed.com

Reliability: ⭐⭐ (DIFFICULT — Indeed actively blocks scrapers)

⚠️ IMPORTANT WARNING:
Indeed has strong anti-scraping measures. This scraper uses
Playwright (a browser automation tool) to mimic a real browser.
Even so, it may get blocked periodically.

WHAT YOU NEED:
- Playwright installed: pip install playwright && playwright install chromium
- This is heavier than other scrapers (opens a real browser window in background)

ALTERNATIVES IF THIS BREAKS:
- Use the Indeed Publisher API (requires approval):
  https://developer.indeed.com/
- Use a scraping service like ScraperAPI or Apify's Indeed scraper
- Focus on the ATS scrapers (Greenhouse/Lever/Ashby) which are more reliable

NOTE: LinkedIn scraping is even harder than Indeed and has been excluded
from this scraper. LinkedIn will ban IPs aggressively. Use their
Jobs API (requires partnership) or focus on other sources.
"""

import os
import asyncio
from db import job_record, save_jobs

SEARCH_QUERIES = [
    "software engineer",
    "product manager",
    "marketing",
]


def scrape(max_jobs: int = None) -> list[dict]:
    """Entry point — runs the async scraper."""
    max_jobs = max_jobs or int(os.getenv("MAX_JOBS_PER_SOURCE", 50))
    return asyncio.run(_scrape_async(max_jobs))


async def _scrape_async(max_jobs: int) -> list[dict]:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  ⚠️  Playwright not installed. Run: pip install playwright && playwright install chromium")
        return []

    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="nl-NL",
        )

        for query in SEARCH_QUERIES:
            if len(jobs) >= max_jobs:
                break

            print(f"  🔍 Indeed: searching '{query}'...")

            try:
                page = await context.new_page()
                url = f"https://nl.indeed.com/vacatures?q={query}&l=Nederland&sort=date"
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)

                # Indeed job cards selector
                # ⚠️ MANUAL CHECK: Indeed changes their HTML frequently
                # If this breaks, inspect nl.indeed.com and find the job card class
                cards = await page.query_selector_all("div.job_seen_beacon, div.tapItem, li.css-5lfssm")

                print(f"     Found {len(cards)} listings")

                for card in cards:
                    if len(jobs) >= max_jobs:
                        break
                    try:
                        job = await _parse_card(card, page)
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        print(f"     ⚠️  Skipping card: {e}")

                await page.close()

            except Exception as e:
                print(f"  ❌ Indeed error for '{query}': {e}")

        await browser.close()

    print(f"  ✅ Indeed: collected {len(jobs)} jobs")
    return jobs


async def _parse_card(card, page) -> dict | None:
    from bs4 import BeautifulSoup

    html = await card.inner_html()
    soup = BeautifulSoup(html, "lxml")

    title_el = soup.find("h2") or soup.find(class_=lambda c: c and "title" in str(c).lower())
    if not title_el:
        return None
    title = title_el.get_text(strip=True)

    company_el = soup.find(class_=lambda c: c and "company" in str(c).lower())
    company = company_el.get_text(strip=True) if company_el else "Unknown"

    location_el = soup.find(class_=lambda c: c and "location" in str(c).lower())
    location = location_el.get_text(strip=True) if location_el else "Nederland"

    link_el = soup.find("a", href=True)
    if not link_el:
        return None
    href = link_el["href"]
    url = "https://nl.indeed.com" + href if href.startswith("/") else href

    return job_record(
        title=title,
        company=company,
        description="",  # Getting full description requires clicking through — skipped for speed
        location=location,
        source_url=url,
        source="indeed",
    )


if __name__ == "__main__":
    jobs = scrape(max_jobs=5)
    for j in jobs:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
    result = save_jobs(jobs)
    print(f"\nSaved: {result}")
