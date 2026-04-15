"""
Test script to manually debug the apply flow.
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

from job_hunter.browser import BrowserManager


async def test_apply_flow():
    """Test the apply flow manually."""

    job_url = "https://www.naukri.com/job-listings-gen-ai-engineer-saven-nova-technologies-hyderabad-chennai-bengaluru-8-to-10-years-080426015716"

    print("=" * 60)
    print("TESTING APPLY FLOW")
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

        print(f"\n[3] Navigating to job: {job_url}")
        await page.goto(job_url, timeout=60000)
        await asyncio.sleep(3)

        print("\n[4] Checking for Apply button...")

        # Test multiple selectors
        selectors = [
            ".apply-button",
            "button.apply-button",
            ".apply-button.n3",
            "a.apply-button",
            "[class*='applyBtn']",
        ]

        for selector in selectors:
            btn = await page.query_selector(selector)
            if btn:
                print(f"    Found: {selector}")
                text = await btn.inner_text()
                print(f"    Button text: {text}")
                break
        else:
            print("    No apply button found!")

            # Get page HTML for debug
            html = await page.content()
            print(f"    Page HTML (first 2000 chars):\n{html[:2000]}")
            return

        print("\n[5] Setting up response interceptor...")

        responses = []

        async def handle_response(response):
            url = response.url
            if "/apply" in url:
                try:
                    data = await response.json()
                    responses.append({"url": url, "data": data})
                    print(f"\n    Caught /apply response!")
                    print(f"    Status code: {data.get('statusCode')}")
                    print(f"    Jobs: {len(data.get('jobs', []))}")
                    if data.get("jobs"):
                        q_count = len(data["jobs"][0].get("questionnaire", []))
                        print(f"    Questions: {q_count}")
                except Exception as e:
                    print(f"    Failed to parse: {e}")

        page.on("response", handle_response)

        print("\n[6] Clicking Apply button...")

        for selector in selectors:
            btn = await page.query_selector(selector)
            if btn:
                await btn.click()
                print(f"    Clicked: {selector}")
                break

        print("\n[7] Waiting for responses (15 seconds)...")

        for i in range(30):
            await asyncio.sleep(0.5)
            if responses:
                print(f"    Got {len(responses)} responses!")
                break
            print(f"    Waiting... ({i + 1}/30)")
        else:
            print("    TIMEOUT - No responses caught!")

            # Check if sidebar opened
            sidebar = await page.query_selector(".chatbot_DrawerContentWrapper")
            if sidebar:
                text = await sidebar.inner_text()
                print(f"\n    Sidebar opened! Content:\n{text[:500]}")
            else:
                print("\n    Sidebar NOT opened!")

        print("\n[8] Final check - check sidebar...")
        sidebar = await page.query_selector(".chatbot_DrawerContentWrapper")
        if sidebar:
            text = await sidebar.inner_text()
            print(f"    Sidebar content:\n{text[:1000]}")

        print("\n[9] Keep browser open for 30 seconds...")
        await asyncio.sleep(30)

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_apply_flow())
