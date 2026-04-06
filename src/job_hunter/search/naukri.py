"""Naukri.com job search using persistent browser session with DOM extraction."""

from __future__ import annotations

import asyncio
import random
import re
from typing import Any

from playwright.async_api import Page

from job_hunter.config import SearchConfig
from job_hunter.resume.schema import ResumeProfile


def _build_search_queries(
    profile: ResumeProfile, search_config: SearchConfig
) -> list[dict[str, str]]:
    """Build search queries: role-only, no skills, no arbitrary cap."""
    queries = []
    locations = (
        profile.preferred_locations[: search_config.max_locations]
        if profile.preferred_locations
        else []
    )
    roles = (
        profile.target_roles[: search_config.max_roles]
        if profile.target_roles
        else ["Technical Lead"]
    )

    for role in roles:
        if locations:
            for loc in locations:
                queries.append({"keyword": role, "location": loc})
        else:
            queries.append({"keyword": role, "location": ""})

    seen = set()
    unique = []
    for q in queries:
        key = f"{q['keyword']}|{q['location']}"
        if key not in seen:
            seen.add(key)
            unique.append(q)

    return unique


def _clean_company(name: str) -> str:
    """Clean company name by removing ratings and 'Posted by' prefixes."""
    if not name:
        return ""
    if name.lower().startswith("posted by"):
        name = name[len("posted by") :].strip()
    name = re.sub(r"\n\d+\.?\d*\s*\n?\d*\s*Reviews?.*", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\d+\.?\d*\s*$", "", name)
    name = re.sub(r"\s*\d*\s*Reviews?$", "", name, flags=re.IGNORECASE)
    return name.strip()


async def _find_job_cards(page: Page) -> list:
    """Find job card elements using multiple selector strategies."""
    selector_sets = [
        ["[data-job-id]", "article[data-job-id]"],
        [".srp-jobtuple", ".tuple", ".jobTuple"],
        [".tuple-label", ".list-item"],
        ['[class*="jobCard"]', '[class*="job-card"]', '[class*="JobCard"]'],
        ['[class*="tuple"]', '[class*="Tuple"]'],
        ["article", 'section[class*="job"]', 'div[class*="job-list"]'],
        ['a[href*="/jobs/"]'],
    ]

    for selectors in selector_sets:
        for sel in selectors:
            try:
                cards = await page.query_selector_all(sel)
                if cards and len(cards) > 0:
                    return cards
            except Exception:
                continue

    return []


async def _extract_job_data(
    card, page: Page, user_skills: list[str] | None = None
) -> dict[str, Any] | None:
    """Extract job data from a card element."""
    try:
        title = ""
        company = ""
        location = ""
        description = ""
        apply_url = ""
        posted_date = ""
        salary = ""
        experience = ""

        # Extract title
        title_el = await card.query_selector(
            'a.title, .title, h2, h3, [class*="title"], [class*="Title"]'
        )
        if title_el:
            title = (await title_el.inner_text()).strip()

        if not title:
            link_el = await card.query_selector("a")
            if link_el:
                title = (await link_el.inner_text()).strip()

        # Find apply URL
        all_links = await card.query_selector_all("a")
        for link in all_links:
            href = await link.get_attribute("href")
            if href and (
                "/jobs/" in href or "/job-details/" in href or "/job-listing/" in href
            ):
                apply_url = (
                    href if href.startswith("http") else f"https://www.naukri.com{href}"
                )
                break

        if not apply_url:
            card_href = await card.get_attribute("href")
            if card_href and ("/jobs/" in card_href or "/job-details/" in card_href):
                apply_url = (
                    card_href
                    if card_href.startswith("http")
                    else f"https://www.naukri.com{card_href}"
                )

        if not apply_url and all_links:
            for link in all_links:
                href = await link.get_attribute("href")
                if href and len(href) > 10:
                    apply_url = (
                        href
                        if href.startswith("http")
                        else f"https://www.naukri.com{href}"
                    )
                    break

        if not title or len(title) < 3:
            return None

        # Extract company rating and review count
        company_rating = ""
        review_count = ""

        # Try to find the company details wrapper
        comp_dtls_el = await card.query_selector(
            '.comp-dtls-wrap, [class*="comp-dtls"], .row2'
        )
        if comp_dtls_el:
            # Extract rating
            rating_el = await comp_dtls_el.query_selector('.rating, [class*="rating"]')
            if rating_el:
                rating_text = await rating_el.inner_text()
                rating_match = re.search(r"(\d+\.?\d*)", rating_text)
                if rating_match:
                    company_rating = rating_match.group(1)

            # Extract review count
            review_el = await comp_dtls_el.query_selector('.review, [class*="review"]')
            if review_el:
                review_text = (await review_el.inner_text()).strip()
                review_match = re.search(
                    r"(\d[\d,]*)\s*Reviews?", review_text, re.IGNORECASE
                )
                if review_match:
                    review_count = review_match.group(1)

        # Extract company - try multiple selectors
        company_selectors = [
            '.company-name, .companyName, [class*="orgName"]',
            'a[href*="/company"]',
            '[class*="comp"]',
            '[class*="Comp"]',
        ]
        for sel in company_selectors:
            company_el = await card.query_selector(sel)
            if company_el:
                company = _clean_company((await company_el.inner_text()).strip())
                if company:
                    break

        # Extract location
        location_selectors = [
            ".location, .jobLocation, .area",
            '[class*="location"]',
            '[class*="Location"]',
        ]
        for sel in location_selectors:
            location_el = await card.query_selector(sel)
            if location_el:
                location = (await location_el.inner_text()).strip()
                if location:
                    break

        # Extract description
        desc_el = await card.query_selector(
            '.description, .jobDescription, .summary, .jd, [class*="desc"]'
        )
        if desc_el:
            description = (await desc_el.inner_text()).strip()[:1000]

        # Extract posted date - try multiple selectors
        date_selectors = [
            ".job-post-day",
        ]
        for sel in date_selectors:
            date_el = await card.query_selector(sel)
            if date_el:
                text = (await date_el.inner_text()).strip()
                if re.match(
                    r"(\d+\s+(?:day|week|month)s?\s+ago|just now|today|yesterday)",
                    text,
                    re.IGNORECASE,
                ):
                    posted_date = text
                    break

        # If still no posted date, try to find it in card text
        if not posted_date:
            card_text = await card.inner_text()
            date_match = re.search(
                r"(\d+\s+(?:day|week|month)s?\s+ago|just now|today|yesterday)",
                card_text,
                re.IGNORECASE,
            )
            if date_match:
                posted_date = date_match.group(1)

        # Extract salary
        salary_selectors = [
            ".salary, .salaryRange, .compensation",
            '[class*="salary"]',
            '[class*="Salary"]',
            '[class*="compensation"]',
        ]
        for sel in salary_selectors:
            salary_el = await card.query_selector(sel)
            if salary_el:
                salary = (await salary_el.inner_text()).strip()
                if salary:
                    break

        # Extract experience
        exp_selectors = [
            ".experience, .expRequired, .requiredExperience",
            '[class*="exp"]',
            '[class*="Exp"]',
        ]
        for sel in exp_selectors:
            exp_el = await card.query_selector(sel)
            if exp_el:
                experience = (await exp_el.inner_text()).strip()
                if experience:
                    break

        # Extract skills: primary from row5 div, fallback to user-skill scan
        skills = await _extract_skills_from_row5(card)
        if not skills and user_skills and description:
            skills = _match_user_skills_in_description(description, user_skills)

        job_data = {
            "title": title,
            "company": company,
            "company_rating": company_rating,
            "review_count": review_count,
            "location": location,
            "work_mode": "remote"
            if "remote" in location.lower() or "work from home" in location.lower()
            else "onsite",
            "experience_required": experience,
            "salary_lpa": salary,
            "job_url": apply_url,
            "job_id": apply_url.split("/")[-1] if "/" in apply_url else "",
            "description": description,
            "posted_date": posted_date,
            "job_board": "naukri",
            "required_skills": skills,
            "data_source": "scraped",
        }
        print(f"  Job extracted: {job_data}")
        return job_data

    except Exception as e:
        print(f"  Error extracting job data: {e}")
        return None


async def _extract_skills_from_row5(card) -> list[str]:
    """Extract key skills from the row5 div on Naukri listing page."""
    try:
        row5_el = await card.query_selector(
            '.row5, [class*="row5"], .tags, [class*="tags"]'
        )
        if row5_el:
            skills_text = (await row5_el.inner_text()).strip()
            if skills_text:
                # Step 1: try proper separators
                parts = re.split(r"[,\|•·]+", skills_text)

                if len(parts) == 1:
                    # Step 2: fallback to camel-case boundary split
                    parts = re.split(r"(?<=[a-z])(?=[A-Z])", skills_text)

                skills = [s.strip() for s in parts if s.strip() and len(s.strip()) > 1]
                return skills

    except Exception:
        pass
    return []


def _match_user_skills_in_description(
    description: str, user_skills: list[str]
) -> list[str]:
    """Scan job description for user's skills using word-boundary regex."""
    matched = []
    desc_lower = description.lower()
    for skill in user_skills:
        skill_lower = skill.lower().strip()
        if not skill_lower or len(skill_lower) < 2:
            continue
        escaped = re.escape(skill_lower)
        pattern = r"\b" + escaped + r"\b"
        if re.search(pattern, desc_lower):
            matched.append(skill_lower)
    return matched


async def scrape_jobs_from_page(
    page: Page,
    keyword: str,
    location: str = "",
    days_old: int = 7,
    max_jobs: int = 100,
    max_pages: int = 1,
    user_skills: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Scrape jobs from Naukri search pages with pagination."""
    print(f"  Searching: {keyword}" + (f" in {location}" if location else ""))

    all_jobs = []
    keyword_encoded = keyword.replace(" ", "%20").replace(".", "%2E")
    loc_encoded = location.replace(" ", "%20").replace(",", "%2C") if location else ""

    for page_num in range(1, max_pages + 1):
        if len(all_jobs) >= max_jobs:
            break

        try:
            if location:
                if page_num == 1:
                    url = f"https://www.naukri.com/{keyword_encoded}-jobs-in-{loc_encoded}?k={keyword_encoded}&jobAge={days_old}"
                else:
                    url = f"https://www.naukri.com/{keyword_encoded}-jobs-{page_num}-in-{loc_encoded}?k={keyword_encoded}&jobAge={days_old}"
            else:
                if page_num == 1:
                    url = f"https://www.naukri.com/{keyword_encoded}-jobs?k={keyword_encoded}&jobAge={days_old}"
                else:
                    url = f"https://www.naukri.com/{keyword_encoded}-jobs-{page_num}?k={keyword_encoded}&jobAge={days_old}"

            print(f"    Page {page_num}: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(2, 5))

            page_text = await page.inner_text("body")
            if "Access Denied" in page_text:
                print(f"    BLOCKED: Naukri is blocking access")
                break

            job_cards = await _find_job_cards(page)
            if not job_cards or len(job_cards) == 0:
                no_results = await page.query_selector(".noResults")
                if no_results:
                    print(f"    No more results on page {page_num}")
                    break
                print(f"    No job cards found on page {page_num}")
                break

            print(f"    Found {len(job_cards)} job cards")

            for card in job_cards:
                if len(all_jobs) >= max_jobs:
                    break
                job = await _extract_job_data(card, page, user_skills=user_skills)
                if job and job.get("title"):
                    job["search_keyword"] = keyword
                    all_jobs.append(job)

            if len(all_jobs) >= max_jobs:
                print(f"    Reached max_jobs limit ({max_jobs})")
                break

            if page_num < max_pages:
                await asyncio.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"    Error on page {page_num}: {e}")
            break

    print(f"    Extracted {len(all_jobs)} jobs from {max_pages} page(s)")
    return all_jobs


def search_naukri(
    profile: ResumeProfile,
    search_config: SearchConfig,
    naukri_config,
    page: Page,
    days_old: int = 7,
    max_jobs_per_query: int = 0,
) -> list[dict[str, Any]]:
    """Search Naukri for jobs using a persistent browser page."""
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()

    if max_jobs_per_query <= 0:
        max_jobs_per_query = 100

    queries = _build_search_queries(profile, search_config)
    print(f"  [INFO] Searching with {len(queries)} queries...")

    all_jobs = []
    seen_keys = set()

    loop = asyncio.get_event_loop()
    delay_min = search_config.delay_min_seconds
    delay_max = search_config.delay_max_seconds

    user_skills = profile.skills + profile.tech_stack
    max_pages = naukri_config.max_pages if naukri_config else 3

    jobs_per_page_estimate = 20
    max_pages_needed = min(
        max_pages,
        (max_jobs_per_query + jobs_per_page_estimate - 1) // jobs_per_page_estimate,
    )
    max_pages_needed = min(max_pages_needed, 5)

    for qi, query in enumerate(queries):
        try:
            jobs = loop.run_until_complete(
                scrape_jobs_from_page(
                    page,
                    query["keyword"],
                    query["location"],
                    days_old=days_old,
                    max_jobs=max_jobs_per_query,
                    max_pages=max_pages_needed,
                    user_skills=user_skills,
                )
            )

            for job in jobs:
                key = f"{job['title'].lower().strip()}|{job['company'].lower().strip()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_jobs.append(job)

            print(f"  Total unique jobs so far: {len(all_jobs)}")

            if qi < len(queries) - 1:
                delay = random.uniform(delay_min, delay_max)
                print(f"  [INFO] Waiting {delay:.1f}s before next query...")
                loop.run_until_complete(asyncio.sleep(delay))

        except Exception as e:
            print(f"  [WARN] Query failed: {e}")
            continue

    if not all_jobs:
        print("[ERROR] No jobs found. Naukri scraping failed.")
        print("  Possible reasons:")
        print("  1. Browser session expired — try running again")
        print("  2. Naukri changed their page structure")
        print("  3. No results for the given keywords/location")

    return all_jobs
