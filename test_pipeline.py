#!/usr/bin/env python3
"""Test script to verify pipeline works with mocked search when Naukri is blocked."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from job_hunter.config import load_config
from job_hunter.resume.parser import load_profile_with_detailed
from job_hunter.browser import BrowserManager
from job_hunter.graph.workflow import build_workflow
from job_hunter.graph.state import JobHunterState
from job_hunter.resume.schema import ResumeProfile


# Mock search function that returns dummy jobs
async def mock_search_naukri(
    profile, search_config, naukri_config, page, days_old, max_jobs_per_query, config
):
    """Mock search function that returns dummy job data."""
    from job_hunter.graph.state import JobListing

    dummy_job = JobListing(
        title="AI Engineer",
        company="Tech Corp",
        location="Bangalore",
        work_mode="Hybrid",
        experience_required="3-5 years",
        salary_lpa="8-12 LPA",
        job_url="https://naukri.com/job1",
        job_id="job1",
        description="We are looking for an AI Engineer with experience in machine learning and deep learning.",
        posted_date="2026-04-01",
        job_board="naukri",
        search_keyword="ai engineer",
    )

    return [dummy_job]


async def test_pipeline_with_mock():
    """Test the pipeline with mocked search function."""
    print("Starting pipeline test with mocked search...")

    # Load config and profile
    config = load_config()
    profile, detailed = load_profile_with_detailed()

    if profile is None:
        print("ERROR: No profile found")
        return False

    print(f"Loaded profile: {profile.name}")

    # Start browser
    browser = BrowserManager(headless=True)
    try:
        page = await browser.start()
        print("Browser started")

        # Build initial state
        initial_state: JobHunterState = {
            "config": config,
            "resume_path": "resume.pdf",
            "force_parse": False,
            "profile": profile,
            "detailed_profile": detailed,
            "raw_jobs": [],
            "scored_jobs": [],
            "shortlisted_jobs": [],
            "csv_path": "",
            "browser_page": page,
            "logged_in_platforms": None,
        }

        # Build workflow
        workflow = build_workflow()

        # Patch the search_naukri function in the search_jobs_node
        import job_hunter.graph.nodes as nodes_module

        original_search_jobs_node = nodes_module.search_jobs_node

        async def patched_search_jobs_node(state):
            """Patched search_jobs_node that uses mock search."""
            from rich.console import Console
            from rich.panel import Panel
            from job_hunter.search.naukri import (
                deduplicate_jobs,
                apply_exclusion_filters,
                apply_title_keyword_filter,
            )
            from job_hunter.graph.helpers import record_run

            console = Console()
            console.print(
                Panel("[bold blue]Searching for jobs...[/]", border_style="blue")
            )

            config = state["config"]
            profile = state["profile"]
            page = state.get("browser_page")

            if profile is None:
                raise RuntimeError("Profile is None, cannot search jobs")

            if page is None:
                raise RuntimeError("Browser page is None, cannot search jobs")

            if config.profile.preferred_roles:
                console.print(
                    f"[dim]Search roles: using user.yaml preferred_roles -> {config.profile.preferred_roles}[/]"
                )
            else:
                console.print(
                    f"[dim]Search roles: using cached profile past_roles -> {profile.past_roles}[/]"
                )

            all_jobs = []
            for platform in config.search.platforms:
                if platform == "naukri":
                    print("[DEBUG] Using mock search for naukri")
                    # Use our mock search function instead of real one
                    jobs = await mock_search_naukri(
                        profile,
                        config.search,
                        config.naukri,
                        page,
                        days_old=1,
                        max_jobs_per_query=getattr(
                            config.search, "max_jobs_per_query", 50
                        )
                        or 50,
                        config=config,
                    )
                    all_jobs.extend(jobs)
                    print(f"[DEBUG] Mock search returned {len(jobs)} jobs")
                    console.print(f"[green]Naukri: found {len(jobs)} jobs[/]")
                    record_run(platform, 1, len(jobs))
                else:
                    console.print(
                        f"[yellow]Platform '{platform}' not yet implemented (Phase 2)[/]"
                    )

            output_dir = Path(__file__).resolve().parents[3] / "output"
            unique_jobs = deduplicate_jobs(all_jobs, output_dir)
            console.print(
                f"[green]After deduplication: {len(unique_jobs)} unique jobs[/]"
            )

            unique_jobs = apply_exclusion_filters(
                unique_jobs,
                config.search.excluded_companies,
                config.search.excluded_keywords,
            )
            if config.search.excluded_companies or config.search.excluded_keywords:
                console.print(
                    f"[green]After exclusion filters: {len(unique_jobs)} jobs[/]"
                )

            unique_jobs = apply_title_keyword_filter(
                unique_jobs, config.search.title_exclude_keywords
            )
            if config.search.title_exclude_keywords:
                console.print(
                    f"[green]After title keyword filter: {len(unique_jobs)} jobs[/]"
                )

            return {"raw_jobs": unique_jobs}

        # Temporarily replace the function
        nodes_module.search_jobs_node = patched_search_jobs_node

        try:
            # Run workflow
            print("Running workflow...")
            result = await workflow.ainvoke(initial_state)

            print("Workflow completed!")
            print(f"CSV output: {result.get('csv_path', 'N/A')}")
            print(f"Jobs found: {len(result.get('raw_jobs', []))}")
            print(f"Jobs scored: {len(result.get('scored_jobs', []))}")
            print(f"Shortlisted: {len(result.get('shortlisted_jobs', []))}")

            # Check if we got expected results
            if len(result.get("raw_jobs", [])) > 0:
                print("SUCCESS: Pipeline processed jobs correctly")
                return True
            else:
                print("ERROR: No jobs were processed")
                return False

        finally:
            # Restore original function
            nodes_module.search_jobs_node = original_search_jobs_node

    finally:
        await browser.close()
        print("Browser closed")


if __name__ == "__main__":
    success = asyncio.run(test_pipeline_with_mock())
    sys.exit(0 if success else 1)
