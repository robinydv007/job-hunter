"""
Test script to test complete apply flow.
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

from job_hunter.browser import BrowserManager
from job_hunter.apply.naukri_apply import apply_to_job
from job_hunter.config import load_config


async def test_complete_apply():
    """Test the complete apply flow."""

    job_url = "https://www.naukri.com/job-listings-ai-engineer-kiash-solution-hyderabad-chennai-bengaluru-5-to-10-years-090426007960"

    print("=" * 60)
    print("TESTING COMPLETE APPLY FLOW")
    print("=" * 60)

    browser = BrowserManager(headless=False)

    try:
        print("\n[1] Starting browser...")
        page = await browser.start()

        print("[2] Logging into Naukri...")
        logged_in = await browser.login_naukri()

        if not logged_in:
            print("    FAILED: Login failed!")
            return
        print("    SUCCESS: Logged in!")

        print("\n[3] Loading config and profile...")
        config = load_config()

        from job_hunter.resume.parser import load_profile_with_detailed

        profile, detailed = load_profile_with_detailed()

        if not profile:
            print("    FAILED: No profile found!")
            return
        print(f"    Profile: {profile.name}, {profile.total_experience_years} years")

        print(f"\n[4] Navigating to job: {job_url}")
        await page.goto(job_url, timeout=60000)
        await asyncio.sleep(3)

        print("\n[5] Testing complete apply flow...")

        job = {
            "job_url": job_url,
            "id": "090426007960",
            "title": "AI Engineer",
            "company": "Kiash Solutions LLP",
            "mandatory_skills": [],
            "optional_skills": [],
        }

        result = await apply_to_job(page, job, profile, config, detailed)

        print(f"\n[6] RESULT:")
        print(f"    Status: {result.status}")
        print(f"    Message: {result.message}")
        print(f"    Error: {result.error}")
        print(f"    Timestamp: {result.timestamp}")

        print("\n[7] Keep browser open for 60 seconds for inspection...")
        await asyncio.sleep(60)

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_complete_apply())
