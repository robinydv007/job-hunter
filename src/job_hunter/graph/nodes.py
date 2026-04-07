"""LangGraph node functions for the job hunter pipeline."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from job_hunter.graph.state import JobHunterState
from job_hunter.graph.helpers import record_run, update_run_stats
from job_hunter.graph.utils import (
    deduplicate_jobs,
    apply_exclusion_filters,
    apply_title_keyword_filter,
)
from job_hunter.resume.parser import (
    load_profile,
    load_detailed_profile,
    load_profile_with_detailed,
    parse_resume_full,
)

console = Console()


def load_config_node(state: JobHunterState) -> dict:
    """Log configuration loaded state (validation already done in CLI)."""
    console.print(Panel("[bold blue]Loading configuration...[/]", border_style="blue"))
    config = state["config"]
    console.print("[green]Configuration loaded successfully[/]")
    return {"config": config}


def parse_resume_node(state: JobHunterState) -> dict:
    """Parse resume or load cached profile.

    If an explicit resume path is provided, always re-parse it with the LLM.
    If no resume path is given, fall back to the cached profile in data/profile.json.
    Uses parse_resume_full for single LLM call extracting both basic + detailed profiles.
    """
    console.print(Panel("[bold blue]Processing resume...[/]", border_style="blue"))
    resume_path = state["resume_path"]
    config = state["config"]
    force_parse = state.get("force_parse", False)

    # Get resume path from config if not provided in state
    if not resume_path:
        resume_path = config.profile.resume_path if config else "resume.pdf"

    # Resolve to absolute path - check if relative (resume.pdf) or absolute
    if resume_path and not Path(resume_path).is_absolute():
        resume_path = Path.cwd() / resume_path

    if not resume_path or not Path(resume_path).exists():
        # Try to load cached profile
        existing, detailed = load_profile_with_detailed()
        if existing and existing.name:
            console.print(f"[green]Using cached profile: {existing.name}[/]")
            if detailed:
                console.print(f"[dim]Detailed profile loaded[/]")
            return {"profile": existing, "detailed_profile": detailed}
        console.print("[red]No resume provided and no cached profile found.[/]")
        raise RuntimeError("No resume path and no cached profile available.")

    console.print(f"[dim]Parsing resume: {resume_path}[/]")
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()

    loop = asyncio.get_event_loop()
    profile, detailed = loop.run_until_complete(
        parse_resume_full(resume_path, force=force_parse)
    )
    console.print(
        f"[green]Profile extracted: {profile.name}, {profile.total_experience_years}y exp, {len(profile.skills)} skills[/]"
    )
    if detailed:
        console.print(f"[dim]Detailed profile generated[/]")
    return {"profile": profile, "detailed_profile": detailed}


def search_jobs_node(state: JobHunterState) -> dict:
    """Search for jobs on configured platforms using persistent browser session."""
    console.print(Panel("[bold blue]Searching for jobs...[/]", border_style="blue"))

    from job_hunter.search.naukri import search_naukri

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
            f"[dim]Search roles: using profile.json past_roles -> {profile.past_roles}[/]"
        )

    all_jobs = []
    for platform in config.search.platforms:
        if platform == "naukri":
            from job_hunter.search.naukri import resolve_freshness

            freshness = resolve_freshness(config.search.freshness, platform)
            console.print(f"[dim]Freshness filter: dd={freshness}[/]")
            max_jobs_per_query = getattr(config.search, "max_jobs_per_query", 50) or 50
            jobs = search_naukri(
                profile,
                config.search,
                config.naukri,
                page,
                days_old=freshness,
                max_jobs_per_query=max_jobs_per_query,
                config=config,
            )
            all_jobs.extend(jobs)
            console.print(f"[green]Naukri: found {len(jobs)} jobs[/]")
            record_run(platform, freshness, len(jobs))
        else:
            console.print(
                f"[yellow]Platform '{platform}' not yet implemented (Phase 2)[/]"
            )

    output_dir = Path(__file__).resolve().parents[3] / "output"
    unique_jobs = deduplicate_jobs(all_jobs, output_dir)
    console.print(f"[green]After deduplication: {len(unique_jobs)} unique jobs[/]")

    unique_jobs = apply_exclusion_filters(
        unique_jobs,
        config.search.excluded_companies,
        config.search.excluded_keywords,
    )
    if config.search.excluded_companies or config.search.excluded_keywords:
        console.print(f"[green]After exclusion filters: {len(unique_jobs)} jobs[/]")

    unique_jobs = apply_title_keyword_filter(
        unique_jobs, config.search.title_exclude_keywords
    )
    if config.search.title_exclude_keywords:
        console.print(f"[green]After title keyword filter: {len(unique_jobs)} jobs[/]")

    return {"raw_jobs": unique_jobs}


def score_jobs_node(state: JobHunterState) -> dict:
    """Score each job against the user profile."""
    console.print(Panel("[bold blue]Scoring jobs...[/]", border_style="blue"))

    profile = state["profile"]
    config = state["config"]
    raw_jobs = state["raw_jobs"]

    if profile is None:
        console.print("[red]ERROR: Profile is None, cannot score jobs[/]")
        return {"scored_jobs": []}

    llm_scoring_config = getattr(config.scoring, "llm_scoring", None)
    use_llm_scoring = llm_scoring_config and llm_scoring_config.enabled

    if use_llm_scoring:
        console.print("[dim]Using LLM-based scoring[/]")
        from job_hunter.scoring.llm_scorer import score_jobs_with_llm_sync

        scored = score_jobs_with_llm_sync(raw_jobs, profile, config)
        threshold = llm_scoring_config.shortlist_threshold

        for result in scored:
            score = result.get("match_score", 0)
            job_data = result.get("job", {})
            title = job_data.get("title", "Unknown")
            company = job_data.get("company", "Unknown")
            color = "green" if score >= threshold else "dim"
            console.print(f"  [{color}]{score}% - {title} at {company}[/]")
    else:
        from job_hunter.scoring.engine import score_job
        from job_hunter.config.constants import load_constants

        constants = load_constants()
        threshold = config.scoring.shortlist_threshold

        scored = []
        for job in raw_jobs:
            job_dict = dict(job)
            result = score_job(job_dict, profile, config, constants)
            scored.append(result)
            score = result.get("match_score", 0)
            job_data = result.get("job", {})
            title = job_data.get("title", "Unknown")
            company = job_data.get("company", "Unknown")
            color = "green" if score >= threshold else "dim"
            console.print(f"  [{color}]{score}% - {title} at {company}[/]")

    return {"scored_jobs": scored, "threshold_used": threshold}


def filter_shortlist_node(state: JobHunterState) -> dict:
    """Filter jobs above the shortlist threshold and select top max_jobs."""
    config = state["config"]
    threshold = state.get("threshold_used") or config.scoring.shortlist_threshold

    shortlisted = [
        j for j in state["scored_jobs"] if j.get("match_score", 0) >= threshold
    ]
    shortlisted.sort(key=lambda j: j.get("match_score", 0), reverse=True)

    if hasattr(config.search, "max_jobs") and config.search.max_jobs > 0:
        shortlisted = shortlisted[: config.search.max_jobs]

    console.print(
        Panel(
            f"[bold green]{len(shortlisted)} jobs shortlisted (threshold: {threshold})[/]",
            border_style="green",
        )
    )

    return {"shortlisted_jobs": shortlisted}


def export_csv_node(state: JobHunterState) -> dict:
    """Export shortlisted jobs to CSV."""
    console.print(Panel("[bold blue]Exporting CSV...[/]", border_style="blue"))

    from job_hunter.export.csv_export import export_to_csv

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).resolve().parents[3] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = str(output_dir / f"shortlist_{timestamp}.csv")

    export_to_csv(state["shortlisted_jobs"], csv_path)
    console.print(f"[green]CSV exported: {csv_path}[/]")
    return {"csv_path": csv_path}


def update_history_node(state: JobHunterState) -> dict:
    """Update run history with final stats after pipeline completes."""
    shortlisted = state.get("shortlisted_jobs", [])
    shortlisted_count = len(shortlisted)
    applied_count = len([j for j in shortlisted if j.get("apply_status") == "Applied"])

    update_run_stats(shortlisted_count, applied_count)
    console.print(
        f"[dim]Run history updated: {shortlisted_count} shortlisted, {applied_count} applied[/]"
    )

    return {}
