# Fix Plan: Freshness, Skills, Scoring, Threshold

## Issue 1: Freshness filter not applied
**Root cause:** `dd` param in Naukri URL only sorts by freshness, doesn't filter. Working URL format uses `jobAge=N` param.
**Fix:** Change URL from `?dd={days_old}` to `?k={keyword}&jobAge={days_old}`

## Issue 2: Skill match = 0
**Root cause:** Scraper extracts skills from hardcoded ~40 keywords in description. Role-only queries return broader jobs.
**Fix:** 
1. Primary: Extract skills from `div.row5` on Naukri listing page — this is where Naukri displays the actual key skills for each job card.
2. Fallback: If row5 not found, scan the job description for the **user's own skills** (from resume profile) using word-boundary regex matching. No static keyword list needed.

## Issue 3: Scores dropped from 62-76 to 31-45
**Root cause:** Direct consequence of Issue 2. Skills = 30% of composite score. With 0% skill match, max possible ~53.
**Fix:** Fixing Issue 2 will automatically fix scores.

## Issue 4: Shortlisted count low
**Root cause:** Threshold lowered to 30 and max_jobs to 100 to compensate for low scores.
**Fix:** After fixes 1-3, restore `shortlist_threshold: 60` and `max_jobs: 10` in `config/user.yaml`.

## Files to change
1. `src/job_hunter/search/naukri.py` — Fix URL format, replace skill extraction with row5 + user-skills fallback
2. `config/user.yaml` — Restore threshold and max_jobs
3. `specs/changelog/2026-04.md` — Log the fixes
4. `specs/phases/phase-1-mvp-pipeline/history.md` — Record fix entries
