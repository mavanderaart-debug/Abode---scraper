# Abode Job Scraper

Scrapes fresh job vacancies from multiple Dutch job boards and ATS platforms,
saves them to your Supabase database, and runs automatically every hour.

---

## Reliability tiers — where to start

| Source | Reliability | Type | Notes |
|---|---|---|---|
| Greenhouse ATS | ⭐⭐⭐⭐⭐ | Public API | Start here. No scraping, just JSON. |
| Lever ATS | ⭐⭐⭐⭐⭐ | Public API | Same as Greenhouse. Very stable. |
| Ashby ATS | ⭐⭐⭐⭐⭐ | Public API | Growing with Dutch tech startups. |
| Nationale Vacaturebank | ⭐⭐⭐⭐ | HTML scraping | Best Dutch-specific source. |
| Werkzoeken | ⭐⭐⭐⭐ | HTML scraping | Good Dutch generalist board. |
| Intermediair | ⭐⭐⭐⭐ | HTML scraping | Good for academic/professional roles. |
| Indeed | ⭐⭐ | Browser automation | Blocks scrapers. Enable with caution. |
| LinkedIn | ❌ | Not included | Actively bans scrapers. Use their API. |

**Recommendation:** Start with just the Tier 1 sources (Greenhouse, Lever, Ashby) 
and add others once things are running smoothly.

---

## Step 1 — Update your Supabase schema

1. Go to your Supabase dashboard → SQL Editor → New query
2. Copy and paste the contents of `supabase-scraper-schema.sql`
3. Click Run

---

## Step 2 — Set up the project locally (optional, for testing)

You need Python 3.11+ installed. Download from python.org if you don't have it.

```bash
# In the abode-scraper folder:
pip install -r requirements.txt

# Copy the example env file
cp .env.example .env

# Edit .env and add your Supabase credentials
# (same URL and key you used for the landing page)
```

Test a single scraper first:
```bash
cd scrapers
python scraper_greenhouse.py
```

Run everything once:
```bash
python main.py --once
```

---

## Step 3 — Deploy to Railway (runs automatically every hour)

Railway will keep the scraper running 24/7 and restart it if it crashes.

1. Go to railway.app and sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Create a NEW GitHub repository called `abode-scraper` and upload all these files
   (same process as the landing page — upload everything in this folder)
4. Connect that repo in Railway
5. Click **Variables** and add:
   - `SUPABASE_URL` → your Supabase project URL
   - `SUPABASE_KEY` → your Supabase anon key
   - `MAX_JOBS_PER_SOURCE` → `50` (or higher if you want more)
6. Railway will deploy automatically — you'll see logs in the Railway dashboard

The scraper will run immediately when deployed, then again every hour.

---

## Adding more companies to Greenhouse/Lever/Ashby

This is the easiest way to expand your job coverage with no risk of breaking.

**For Greenhouse:**
1. Open `scrapers/scraper_greenhouse.py`
2. Find the `COMPANIES` list
3. Add the company's Greenhouse slug (find it at `boards.greenhouse.io/SLUG`)

**For Lever:**
1. Open `scrapers/scraper_lever.py`
2. Find the `COMPANIES` list  
3. Add the company's Lever slug (find it at `jobs.lever.co/SLUG`)

**For Ashby:**
1. Open `scrapers/scraper_ashby.py`
2. Find the `COMPANIES` list
3. Add the slug (find it at `jobs.ashbyhq.com/SLUG`)

---

## Adjusting search terms

In each HTML-based scraper (`scraper_nvb.py`, `scraper_werkzoeken.py`, `scraper_intermediair.py`),
find the `SEARCH_QUERIES` list near the top and edit it to match the roles your users are 
looking for.

---

## What to do if an HTML scraper breaks

HTML scrapers break when the job board redesigns their website. This is normal.

When a scraper stops finding jobs:
1. Open the job board in your browser (e.g. nationalevacaturebank.nl)
2. Right-click on a job card → "Inspect Element"
3. Find the HTML tag/class that wraps the job card
4. Update the selector in the scraper — look for comments marked ⚠️ MANUAL CHECK

---

## Viewing scraped jobs

In your Supabase dashboard:
- **Table Editor → jobs** — see all jobs
- **SQL Editor** → run: `select * from jobs_by_source` — see counts by source

---

## File structure

```
abode-scraper/
├── main.py                      # Runs all scrapers + hourly scheduler
├── db.py                        # Supabase connection + save logic
├── http_client.py               # HTTP helper with anti-blocking
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── Procfile                     # Railway start command
├── railway.toml                 # Railway config
├── supabase-scraper-schema.sql  # Run this in Supabase first
└── scrapers/
    ├── scraper_greenhouse.py    # Greenhouse ATS (API)
    ├── scraper_lever.py         # Lever ATS (API)
    ├── scraper_ashby.py         # Ashby ATS (API)
    ├── scraper_nvb.py           # Nationale Vacaturebank
    ├── scraper_werkzoeken.py    # Werkzoeken.nl
    ├── scraper_intermediair.py  # Intermediair.nl
    └── scraper_indeed.py        # Indeed (disabled by default)
```
