"""LangGraph node functions for the job hunter pipeline."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from job_hunter.graph.state import JobHunterState
from job_hunter.resume.parser import load_profile, parse_resume

console = Console()

NAUKRI_FRESHNESS_VALUES = [1, 3, 7, 15, 30]


def _get_run_history_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "run_history.json"


def _load_run_history() -> list[dict]:
    path = _get_run_history_path()
    if not path.exists():
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_run_history(history: list[dict]) -> None:
    path = _get_run_history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)


def resolve_freshness(config_freshness: int, platform: str = "naukri") -> int:
    """Resolve freshness value based on config and run history.

    Args:
        config_freshness: User-configured freshness (0=auto, 1/3/7/15/30=days)
        platform: Platform name (default: naukri)

    Returns:
        Resolved freshness value for the dd URL parameter
    """
    history = _load_run_history()
    platform_history = [h for h in history if h.get("platform") == platform]

    if config_freshness > 0:
        if not platform_history:
            return config_freshness
        last_run = platform_history[-1]
        last_ts = datetime.fromisoformat(last_run["timestamp"])
        days_since = (datetime.now() - last_ts).days
        auto_value = _map_days_to_freshness(days_since)
        return max(config_freshness, auto_value)

    if not platform_history:
        return 7

    last_run = platform_history[-1]
    last_ts = datetime.fromisoformat(last_run["timestamp"])
    days_since = (datetime.now() - last_ts).days
    return _map_days_to_freshness(days_since)


def _map_days_to_freshness(days: int) -> int:
    """Map days since last run to the smallest Naukri freshness value >= days."""
    for value in NAUKRI_FRESHNESS_VALUES:
        if value >= days:
            return value
    return 30


def record_run(platform: str, freshness_used: int, jobs_found: int) -> None:
    """Append a run record to data/run_history.json."""
    history = _load_run_history()
    history.append(
        {
            "timestamp": datetime.now().isoformat(),
            "freshness_used": freshness_used,
            "jobs_found": jobs_found,
            "platform": platform,
        }
    )
    _save_run_history(history)


console = Console()


def load_config_node(state: JobHunterState) -> dict:
    """Log configuration loaded state (validation already done in CLI)."""
    console.print(Panel("[bold blue]Loading configuration...[/]", border_style="blue"))
    config = state["config"]
    console.print("[green]Configuration loaded successfully[/]")
    return {"config": config, "profile_validated": True}


def parse_resume_node(state: JobHunterState) -> dict:
    """Parse resume or load cached profile."""
    console.print(Panel("[bold blue]Processing resume...[/]", border_style="blue"))
    resume_path = state["resume_path"]

    existing = load_profile()
    if existing and existing.name:
        console.print(f"[green]Using cached profile: {existing.name}[/]")
        return {"profile": existing}

    console.print("[dim]Parsing resume with LLM...[/]")
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()

    loop = asyncio.get_event_loop()
    profile = loop.run_until_complete(parse_resume(resume_path))
    console.print(
        f"[green]Profile extracted: {profile.name}, {profile.total_experience_years}y exp, {len(profile.skills)} skills[/]"
    )
    return {"profile": profile}


def search_jobs_node(state: JobHunterState) -> dict:
    """Search for jobs on configured platforms using persistent browser session."""
    console.print(Panel("[bold blue]Searching for jobs...[/]", border_style="blue"))

    from job_hunter.search.naukri import search_naukri

    config = state["config"]
    profile = state["profile"]
    page = state.get("browser_page")

    if profile is None:
        console.print("[red]ERROR: Profile is None, cannot search jobs[/]")
        return {"raw_jobs": [], "errors": ["Profile not parsed"]}

    if page is None:
        console.print("[red]ERROR: Browser page is None, cannot search jobs[/]")
        return {"raw_jobs": [], "errors": ["Browser not initialized"]}

    all_jobs = []
    for platform in config.search.platforms:
        if platform == "naukri":
            freshness = resolve_freshness(config.search.freshness, platform)
            console.print(f"[dim]Freshness filter: dd={freshness}[/]")
            jobs = search_naukri(
                profile, config.search, page, days_old=freshness, max_jobs_per_query=100
            )
            all_jobs.extend(jobs)
            console.print(f"[green]Naukri: found {len(jobs)} jobs[/]")
            record_run(platform, freshness, len(jobs))
        else:
            console.print(
                f"[yellow]Platform '{platform}' not yet implemented (Phase 2)[/]"
            )

    # Deduplicate by title + company + location fingerprint
    seen = set()

    # Pre-populate seen set with jobs from past runs
    output_dir = Path(__file__).resolve().parents[3] / "output"
    if output_dir.exists():
        import csv

        for csv_file in output_dir.glob("shortlist_*.csv"):
            try:
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        fp = hashlib.md5(
                            f"{row.get('job_title', '')}|{row.get('company', '')}|{row.get('location', '')}".lower().encode()
                        ).hexdigest()
                        seen.add(fp)
            except Exception as e:
                console.print(
                    f"[dim]Warning: Could not read past CSV {csv_file.name} for deduplication.[/]"
                )

    unique_jobs = []
    for job in all_jobs:
        fp = hashlib.md5(
            f"{job.get('title', '')}|{job.get('company', '')}|{job.get('location', '')}".lower().encode()
        ).hexdigest()
        if fp not in seen:
            seen.add(fp)
            unique_jobs.append(job)

    console.print(f"[green]After deduplication: {len(unique_jobs)} unique jobs[/]")

    # Apply exclusion filters from config
    excluded_companies = [c.lower() for c in config.search.excluded_companies]
    excluded_keywords = [k.lower() for k in config.search.excluded_keywords]

    if excluded_companies or excluded_keywords:
        filtered = []
        for job in unique_jobs:
            company = job.get("company", "").lower()
            title = job.get("title", "").lower()
            description = job.get("description", "").lower()
            text = f"{title} {description}"

            if excluded_companies and company in excluded_companies:
                continue
            if excluded_keywords and any(kw in text for kw in excluded_keywords):
                continue
            filtered.append(job)
        console.print(f"[green]After exclusion filters: {len(filtered)} jobs[/]")
        unique_jobs = filtered

    return {"raw_jobs": unique_jobs}


def score_jobs_node(state: JobHunterState) -> dict:
    """Score each job against the user profile."""
    console.print(Panel("[bold blue]Scoring jobs...[/]", border_style="blue"))

    from job_hunter.scoring.engine import score_job

    profile = state["profile"]
    config = state["config"]
    raw_jobs = state["raw_jobs"]

    if profile is None:
        console.print("[red]ERROR: Profile is None, cannot score jobs[/]")
        return {"scored_jobs": []}

    scored = []
    for job in raw_jobs:
        job_dict = dict(job)
        result = score_job(job_dict, profile, config)
        scored.append(result)
        score = result.get("match_score", 0)
        job_data = result.get("job", {})
        title = job_data.get("title", "Unknown")
        company = job_data.get("company", "Unknown")
        color = "green" if score >= config.scoring.shortlist_threshold else "dim"
        console.print(f"  [{color}]{score}% - {title} at {company}[/]")

    return {"scored_jobs": scored}


def filter_shortlist_node(state: JobHunterState) -> dict:
    """Filter jobs above the shortlist threshold and select top max_jobs."""
    config = state["config"]
    threshold = config.scoring.shortlist_threshold

    # Filter and sort by score descending
    shortlisted = [
        j for j in state["scored_jobs"] if j.get("match_score", 0) >= threshold
    ]
    shortlisted.sort(key=lambda j: j.get("match_score", 0), reverse=True)

    # Take top N
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
