# Job Hunter Agent — Implementation Plan

**Version:** v1.0  
**Status:** In progress

---

## What We Know

- Naukri blocks ALL headless browsers (403 from Akamai/CloudFront)
- **Non-headless (`headless=False`) works** — login succeeds, search pages load
- Existing working code at `D:\Development\Projects\ai\test\naukri\finder.py`
- Key success factors: `headless=False`, single persistent browser session, correct URL format, proper DOM selectors
- Freshness filter via `dd` parameter (days old) is mandatory
- Job data loads via Next.js SPA — need to wait for DOM rendering + scroll

---

## Option 1: Persistent Browser Session + DOM Selectors (Primary)

**Approach:** Single visible browser session, login once, search multiple queries, extract via DOM selectors

**Key components:**
- `BrowserManager` class — persistent Playwright session, `headless=False`
- Login once at startup, reuse same page for all searches
- Search URL: `https://www.naukri.com/keyword-jobs-in-location?dd=7`
- Extract via DOM selectors: `[data-job-id]`, `.srp-jobtuple`, `.tuple`, etc.
- Scroll to load more jobs, deduplicate by title+company

---

## Option 2: Text-Based Extraction (Fallback)

**Approach:** Same persistent browser, extract jobs from `page.inner_text("body")` instead of DOM selectors

**Changes needed:** Only the extraction logic in `naukri.py`

---

## Option 3: Apify Naukri Job Scraper API (Last Resort)

**Approach:** Use Apify's pre-built Naukri scraper via their API
- Free tier = 1000 jobs (~$0.0023/job)
- Handles all anti-detection, proxies, pagination automatically

---

## Execution Order

1. **Option 1** — BrowserManager + DOM-based extraction
2. **If DOM selectors fail** → Option 2 (text parsing)
3. **If both fail** → Option 3 (Apify API)

---

## Additional Fixes Needed

- **Freshness filter** — add `dd` parameter to search URLs (configurable, default 7 days)
- **Skills extraction** — parse skills from job description text
- **Location extraction** — handle "Hybrid - Gurugram" format
- **Company cleaning** — strip ratings, "Posted by" prefixes
- **Scoring improvement** — use extracted skills for proper matching
