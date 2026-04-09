"""
Explore Naukri Apply API Flow

This script explores the Naukri apply flow by intercepting API calls.
Run this to understand how the /apply and /respond APIs work.

Usage:
    python scripts/explore_apply_api.py
"""

import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

from job_hunter.browser import BrowserManager


async def explore_apply_api():
    """Explore Naukri apply API flow."""

    job_url = "https://www.naukri.com/job-listings-full-stack-ai-developer-agentic-ai-teqfocus-consulting-pune-5-to-10-years-250326025777?src=cluster&sid=17757311497391557_1&xp=11&px=1&nignbevent_src=jobsearchDeskGNB"

    print("=" * 60)
    print("NAUKRI APPLY API EXPLORATION")
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

        print(f"\n[3] Navigating to job detail page...")
        await page.goto(job_url, timeout=60000)
        await asyncio.sleep(3)

        print("\n[4] Setting up API interception...")

        captured_responses = []

        async def handle_response(response):
            url = response.url
            if "/apply" in url or "/respond" in url:
                try:
                    data = await response.json()
                    captured_responses.append(
                        {"url": url, "method": response.request.method, "data": data}
                    )
                    print(f"\n--- API CALL: {response.request.method} {url}")
                    print(json.dumps(data, indent=2)[:2000])
                except Exception as e:
                    print(f"    Could not parse response: {e}")

        page.on("response", handle_response)

        print("\n[5] Clicking Apply button...")
        apply_button = await page.query_selector(".apply-button")

        if apply_button:
            await apply_button.click()
            print("    Clicked Apply button")

            print("\n[6] Waiting for API responses (60 seconds)...")
            print("    NOTE: You can manually answer questions in the browser sidebar.")
            print("    I'll capture all API calls during this time...")
            await asyncio.sleep(60)

            print(f"\n[7] Total API responses captured: {len(captured_responses)}")

            for i, resp in enumerate(captured_responses, 1):
                print(f"\n{'=' * 60}")
                print(f"RESPONSE #{i}: {resp['method']} {resp['url']}")
                print("=" * 60)
                print(json.dumps(resp["data"], indent=2))

            print("\n[8] Checking sidebar content...")
            sidebar = await page.query_selector(".chatbot_DrawerContentWrapper")

            if sidebar:
                sidebar_content = await sidebar.inner_text()
                print(f"\nSidebar content (first 1000 chars):")
                print(sidebar_content[:1000])
            else:
                print("    Sidebar not found")

            print("\n[9] Checking for 'Applied' badge...")
            applied_badge = await page.query_selector(
                ".applied-badge, [class*='Applied']"
            )

            if applied_badge:
                print("    Found: Applied badge present")
            else:
                print("    No Applied badge found")
        else:
            print("    FAILED: Could not find Apply button")

        print("\n" + "=" * 60)
        print("EXPLORATION COMPLETE")
        print("=" * 60)

        output_file = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "explore_apply_api_captured.json"
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(captured_responses, f, indent=2)

        print(f"\nCaptured responses saved to: {output_file}")

        print("\n[10] Keeping browser open for 30 seconds for manual inspection...")
        await asyncio.sleep(30)

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(explore_apply_api())
