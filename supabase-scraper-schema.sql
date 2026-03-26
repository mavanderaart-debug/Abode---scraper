-- ============================================================
-- Run this in Supabase > SQL Editor to update your jobs table
-- for scraper compatibility
-- ============================================================

-- Add 'source' column to track where each job came from
alter table public.jobs
  add column if not exists source text;

-- Add unique constraint on source_url to prevent duplicates
-- (safe to run even if constraint already exists)
alter table public.jobs
  drop constraint if exists jobs_source_url_unique;

alter table public.jobs
  add constraint jobs_source_url_unique unique (source_url);

-- Allow the scraper (anon key) to insert jobs
create policy if not exists "Scraper can insert jobs"
  on public.jobs
  for insert
  to anon
  with check (true);

-- Allow the scraper to read jobs (for duplicate checking)
create policy if not exists "Scraper can read jobs"
  on public.jobs
  for select
  to anon
  using (true);

-- View: see all jobs with their source
-- Useful for checking what came from where
create or replace view public.jobs_by_source as
  select source, count(*) as total, max(created_at) as last_scraped
  from public.jobs
  group by source
  order by total desc;
