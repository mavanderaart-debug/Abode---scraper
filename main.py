"""
main.py — Abode Job Scraper Orchestrator
=========================================
This is the main file that runs all scrapers and saves results to Supabase.

USAGE:
  Run once:       python main.py
  Run on Railway: this file is the entry point (set in Procfile)

ADDING/REMOVING SCRAPERS:
  Add or comment out scrapers in the SCRAPERS list below.
  Start with just Greenhouse + Lever + Ashby for reliability.
  Add NVB/Werkzoeken/Intermediair once those are working.
"""

import sys
import os
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Add scrapers to path ──────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scrapers"))

from db import save_jobs


# ── Configure which scrapers to run ──────────────────────────────────────────
# Comment out any scraper you want to temporarily disable
SCRAPERS = [
    # ✅ TIER 1: Most reliable (API-based, start here)
    ("Greenhouse ATS",  "scraper_greenhouse",  True),
    ("Lever ATS",       "scraper_lever",       True),
    ("Ashby ATS",       "scraper_ashby",       True),

    # ✅ TIER 2: Good reliability (HTML scraping, Dutch job boards)
    ("Nationale Vacaturebank", "scraper_nvb",          True),
    ("Werkzoeken",             "scraper_werkzoeken",   True),
    ("Intermediair",           "scraper_intermediair", True),

    # ⚠️ TIER 3: Harder to scrape (may need maintenance)
    ("Indeed",          "scraper_indeed",      False),  # Set to True to enable
    # LinkedIn is not included — blocks scrapers aggressively
]


def run_all_scrapers():
    """Run all enabled scrapers and save results to Supabase."""
    start_time = datetime.now()
    print(f"\n{'='*55}")
    print(f"🏠 Abode Scraper — {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")

    total_saved = 0
    total_skipped = 0
    total_errors = 0

    for scraper_name, module_name, enabled in SCRAPERS:
        if not enabled:
            print(f"⏭️  Skipping {scraper_name} (disabled)")
            continue

        print(f"\n📋 Running: {scraper_name}")
        print(f"   {'─'*40}")

        try:
            # Dynamically import the scraper module
            import importlib
            module = importlib.import_module(module_name)

            # Run the scraper
            jobs = module.scrape()

            if jobs:
                result = save_jobs(jobs)
                total_saved += result["saved"]
                total_skipped += result["skipped"]
                total_errors += result["errors"]
                print(f"   💾 Saved: {result['saved']} | Skipped: {result['skipped']} | Errors: {result['errors']}")
            else:
                print(f"   ℹ️  No jobs collected")

        except ModuleNotFoundError:
            print(f"   ❌ Module '{module_name}' not found — skipping")
        except Exception as e:
            print(f"   ❌ Scraper failed: {e}")
            total_errors += 1

        # Brief pause between scrapers to be polite
        time.sleep(2)

    # ── Summary ──────────────────────────────────────────────────────────────
    duration = (datetime.now() - start_time).seconds
    print(f"\n{'='*55}")
    print(f"✅ Run complete in {duration}s")
    print(f"   Total saved:   {total_saved}")
    print(f"   Total skipped: {total_skipped} (duplicates)")
    print(f"   Total errors:  {total_errors}")
    print(f"{'='*55}\n")


def run_scheduler():
    """Run the scraper on a schedule (every hour)."""
    print("🕐 Scheduler started — running every hour")
    print("   Press Ctrl+C to stop\n")

    # Run immediately on start
    run_all_scrapers()

    # Then schedule to run every hour
    schedule.every(1).hours.do(run_all_scrapers)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    # If the script is called with --once, run once and exit
    # Otherwise run on a schedule (for Railway deployment)
    if "--once" in sys.argv:
        run_all_scrapers()
    else:
        run_scheduler()
