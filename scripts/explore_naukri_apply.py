"""
Explore Naukri Apply Flow - Detailed Version

This script thoroughly explores the Naukri apply sidebar to find all form fields.
"""

import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

from job_hunter.browser import BrowserManager


async def explore_apply_flow():
    """Explore Naukri job detail page and apply form using BrowserManager."""

    job_url = "https://www.naukri.com/job-listings-technical-lead-tata-consultancy-services-kolkata-pune-chennai-5-to-10-years-180326036328?src=jobsearchDesk&sid=17750431827535292&xp=2&px=1"

    print("=" * 60)
    print("NAUKRI APPLY FLOW EXPLORATION - DETAILED")
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
        await asyncio.sleep(5)

        # Find and click apply
        print("\n[4] Looking for Apply button...")
        apply_button = await page.query_selector(".apply-button")
        if apply_button:
            print("    Found Apply button")
            await apply_button.click()
            await asyncio.sleep(3)
            print("    Clicked Apply - sidebar should be open")
        else:
            print("    FAILED: Could not find Apply button")

        # Wait for sidebar content to load
        await asyncio.sleep(3)

        # Get full HTML to analyze structure
        print("\n[5] Analyzing page structure...")

        # Get all elements with data attributes
        data_attrs = await page.evaluate("""() => {
            const elements = document.querySelectorAll('[data-section], [id*="resume"], [id*="field"], [class*="field"]');
            return Array.from(elements).map(el => ({
                tag: el.tagName,
                id: el.id,
                class: el.className,
                dataAttr: Object.keys(el.dataset).map(k => k + '=' + el.dataset[k])
            }));
        }""")

        if data_attrs:
            print(f"    Found {len(data_attrs)} elements with data attributes")

        # Get all inputs, selects, textareas
        print("\n[6] Finding all form elements...")

        all_elements = await page.evaluate("""() => {
            const results = [];
            
            // Find all inputs
            document.querySelectorAll('input, select, textarea').forEach(el => {
                results.push({
                    tag: el.tagName,
                    type: el.type || 'text',
                    id: el.id,
                    name: el.name,
                    placeholder: el.placeholder,
                    required: el.required
                });
            });
            
            return results;
        }""")

        print(f"    Total form elements: {len(all_elements)}")

        # Print unique fields
        seen = set()
        unique_fields = []
        for f in all_elements:
            key = f.get("id") or f.get("name") or str(f)
            if key and key not in seen:
                seen.add(key)
                unique_fields.append(f)

        print(f"\n    Unique form fields ({len(unique_fields)}):")
        print("    " + "-" * 50)
        for i, field in enumerate(unique_fields[:50], 1):
            print(
                f"    {i}. {field.get('tag')}: {field.get('type')} | id={field.get('id')} | name={field.get('name')}"
            )

        # Get page content for more analysis
        print("\n[7] Getting page content for analysis...")
        content = await page.content()

        # Look for specific keywords
        keywords = [
            "resume",
            "name",
            "email",
            "phone",
            "notice",
            "ctc",
            "salary",
            "period",
            "answer",
            "question",
        ]
        print(f"\n    Searching for: {keywords}")

        for kw in keywords:
            count = content.lower().count(kw)
            if count > 0:
                print(f"    - '{kw}': {count} occurrences")

        # Try to find form by different selectors
        print("\n[8] Trying additional selectors...")

        additional_selectors = [
            ".candidate-details-section",
            ".resume-upload-section",
            ".application-form",
            ".form-container",
            ".quick-apply-form",
            "#resumeUpload",
            '[name*="resume"]',
            '[id*="resume"]',
        ]

        for sel in additional_selectors:
            el = await page.query_selector(sel)
            if el:
                print(f"    Found: {sel}")

        # Save findings
        output_file = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "naukri_apply_form_detailed.json"
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)

        findings = {
            "job_url": job_url,
            "form_elements": unique_fields,
            "data_attributes": data_attrs[:20] if data_attrs else [],
        }

        with open(output_file, "w") as f:
            json.dump(findings, f, indent=2)

        print(f"\n    Saved to: {output_file}")

        # Keep open for manual inspection
        print("\n[9] Keeping browser open for 30 seconds...")
        await asyncio.sleep(30)

    finally:
        await browser.close()

    print("\n" + "=" * 60)
    print("EXPLORATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(explore_apply_flow())
