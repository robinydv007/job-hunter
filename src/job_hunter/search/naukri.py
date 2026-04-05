"""Naukri.com job search using persistent browser session with DOM extraction."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from playwright.async_api import Page

from job_hunter.config import SearchConfig
from job_hunter.resume.schema import ResumeProfile


def _build_search_queries(
    profile: ResumeProfile, search_config: SearchConfig
) -> list[dict[str, str]]:
    """Build search queries with keywords and optional location."""
    queries = []
    # Only use locations from config, not from resume's location_preference
    locations = profile.preferred_locations if profile.preferred_locations else []

    roles = profile.target_roles[:3] if profile.target_roles else ["Technical Lead"]
    key_skills = profile.tech_stack[:3] if profile.tech_stack else profile.skills[:5]

    for role in roles:
        for skill in key_skills:
            keyword = f"{role} {skill}".strip()
            if locations:
                for loc in locations[:3]:
                    queries.append(
                        {
                            "keyword": keyword,
                            "location": loc,
                        }
                    )
            else:
                queries.append(
                    {
                        "keyword": keyword,
                        "location": "",
                    }
                )

    seen = set()
    unique = []
    for q in queries:
        key = f"{q['keyword']}|{q['location']}"
        if key not in seen:
            seen.add(key)
            unique.append(q)

    return unique[:10]


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


async def _extract_job_data(card, page: Page) -> dict[str, Any] | None:
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
            description = (await desc_el.inner_text()).strip()[:500]

        # Extract posted date - try multiple selectors
        date_selectors = [
            ".date, .postedDate, .days-old, .time",
            '[class*="date"]',
            '[class*="Date"]',
            '[class*="days"]',
            '[class*="Days"]',
            '[class*="posted"]',
            '[class*="Posted"]',
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

        # Extract skills from description
        skills = []
        if description:
            tech_keywords = [
                "node.js",
                "nodejs",
                "react",
                "react.js",
                "python",
                "java",
                "aws",
                "docker",
                "kubernetes",
                "typescript",
                "javascript",
                "mongodb",
                "postgres",
                "postgresql",
                "mysql",
                "redis",
                "kafka",
                "rabbitmq",
                "graphql",
                "microservices",
                "angular",
                "vue",
                "nestjs",
                "express",
                "django",
                "flask",
                "spring",
                "golang",
                "azure",
                "gcp",
                "terraform",
                "jenkins",
                "ci/cd",
                "system design",
                "distributed systems",
                "observability",
                "fastapi",
                "temporal",
                "php",
                "laravel",
                "shopify",
            ]
            for kw in tech_keywords:
                if kw in description.lower():
                    skills.append(kw)

        return {
            "title": title,
            "company": company,
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

    except Exception as e:
        print(f"  Error extracting job data: {e}")
        return None


async def scrape_jobs_from_page(
    page: Page,
    keyword: str,
    location: str = "",
    days_old: int = 7,
    max_jobs: int = 20,
) -> list[dict[str, Any]]:
    """Scrape jobs from a Naukri search page using DOM selectors."""
    print(f"  Searching: {keyword}" + (f" in {location}" if location else ""))

    try:
        # Build search URL with freshness filter
        keyword_encoded = keyword.replace(" ", "%20").replace(".", "%2E")
        if location:
            loc_encoded = location.replace(" ", "%20").replace(",", "%2C")
            url = f"https://www.naukri.com/{keyword_encoded}-jobs-in-{loc_encoded}?dd={days_old}"
        else:
            url = f"https://www.naukri.com/{keyword_encoded}-jobs?dd={days_old}"

        print(f"    URL: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Check if blocked
        page_text = await page.inner_text("body")
        if "Access Denied" in page_text:
            print(f"  BLOCKED: Naukri is blocking access")
            return []

        # Find job cards
        jobs = []
        job_cards = await _find_job_cards(page)
        print(f"    Found {len(job_cards)} job cards")

        for card in job_cards[:max_jobs]:
            job = await _extract_job_data(card, page)
            if job and job.get("title"):
                jobs.append(job)

        # Scroll to load more
        if len(jobs) < max_jobs:
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 600)")
                await asyncio.sleep(2)
                more_cards = await _find_job_cards(page)
                if len(more_cards) > len(job_cards):
                    job_cards = more_cards
                    for card in job_cards[len(jobs) : max_jobs]:
                        job = await _extract_job_data(card, page)
                        if job and job.get("title"):
                            jobs.append(job)
                if len(jobs) >= max_jobs:
                    break

    except Exception as e:
        print(f"  Error scraping: {e}")
        return []

    print(f"    Extracted {len(jobs)} jobs")
    return jobs


def search_naukri(
    profile: ResumeProfile,
    search_config: SearchConfig,
    page: Page,
    days_old: int = 7,
    max_jobs_per_query: int = 15,
) -> list[dict[str, Any]]:
    """Search Naukri for jobs using a persistent browser page."""
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()

    queries = _build_search_queries(profile, search_config)
    print(f"  [INFO] Searching with {len(queries)} queries...")

    all_jobs = []
    seen_keys = set()

    loop = asyncio.get_event_loop()

    for qi, query in enumerate(queries):
        if len(all_jobs) >= 150:
            break

        try:
            jobs = loop.run_until_complete(
                scrape_jobs_from_page(
                    page,
                    query["keyword"],
                    query["location"],
                    days_old=days_old,
                    max_jobs=min(max_jobs_per_query, 150 - len(all_jobs)),
                )
            )

            for job in jobs:
                key = f"{job['title'].lower().strip()}|{job['company'].lower().strip()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_jobs.append(job)

            print(f"  Total unique jobs so far: {len(all_jobs)}")

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
