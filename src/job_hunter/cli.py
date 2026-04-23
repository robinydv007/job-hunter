"""CLI entry point for Job Hunter Agent."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from job_hunter.config import (
    bootstrap_config,
    build_effective_config,
)
from job_hunter.graph.workflow import build_workflow
from job_hunter.browser import BrowserManager

console = Console()


@click.group()
def cli():
    """Job Hunter Agent — AI-powered job search automation."""
    pass


@cli.command()
@click.option(
    "--resume",
    "-r",
    type=click.Path(exists=True),
    default=None,
    help="Path to resume file (PDF, DOCX, or TXT)",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default=None,
    help="Path to config YAML file",
)
@click.option(
    "--headless",
    is_flag=True,
    default=False,
    help="Run browser in headless mode (not recommended for Naukri)",
)
@click.option(
    "--force-parse",
    is_flag=True,
    default=False,
    help="Force re-parse resume even if a cached profile already exists",
)
def run(resume: str | None, config: str | None, headless: bool, force_parse: bool):
    """Run the full job hunter pipeline."""
    console.print(
        Panel("[bold green]Job Hunter Agent[/] Starting...", border_style="green")
    )

    bootstrap_result = bootstrap_config(resume_path=resume if resume else None)
    effective_config = bootstrap_result["config"]

    app_config = effective_config["app"]

    cached_profile_path = Path("data" / "profile_cache.json")
    explicit_resume = (
        resume is not None
    )  # True only when --resume was explicitly passed

    if resume is None:
        if Path("resume.pdf").exists():
            resume = "resume.pdf"
        else:
            console.print(
                "[red]No resume file provided and 'resume.pdf' not found in root directory.[/]"
            )
            console.print(
                "Please use --resume to specify one or place 'resume.pdf' in the root directory."
            )
            raise SystemExit(1)

    if not explicit_resume and not force_parse and cached_profile_path.exists():
        console.print(
            "[dim]Cached profile found — skipping resume parse. Use --force-parse to re-parse.[/]"
        )
        resume = None  # signals parse_resume_node to use cache
    elif force_parse and not explicit_resume:
        if not resume and Path("resume.pdf").exists():
            resume = "resume.pdf"
        console.print("[dim]Forcing resume re-parse (--force-parse)[/]")
    elif explicit_resume:
        console.print(f"[dim]Parsing resume: {resume}[/]")

    async def run_pipeline():
        browser = BrowserManager(headless=headless)
        page = await browser.start()

        try:
            logged_in = await browser.login_naukri()
            if not logged_in:
                console.print("[red]Failed to login to Naukri. Check credentials.[/]")
                await browser.close()
                raise SystemExit(1)

            initial_state = {
                "config": app_config,
                "resume_path": resume,
                "force_parse": force_parse,
                "profile": None,
                "detailed_profile": None,
                "raw_jobs": [],
                "scored_jobs": [],
                "shortlisted_jobs": [],
                "csv_path": "",
                "browser_page": page,
            }

            workflow = build_workflow()
            result = await workflow.ainvoke(initial_state)

            console.print(
                Panel("[bold green]Pipeline complete![/]", border_style="green")
            )
            console.print(f"CSV output: [bold]{result.get('csv_path', 'N/A')}[/]")
            console.print(f"Jobs found: {len(result.get('raw_jobs', []))}")
            console.print(f"Jobs scored: {len(result.get('scored_jobs', []))}")
            console.print(f"Shortlisted: {len(result.get('shortlisted_jobs', []))}")

        finally:
            await browser.close()

    asyncio.run(run_pipeline())


@cli.command()
def status():
    """Show current pipeline status and cached data."""
    from job_hunter.resume.parser import load_profile_from_cache

    profile, _ = load_profile_from_cache()
    if profile:
        console.print(f"[green]Cached profile: {profile.name}[/]")
        console.print(f"  Skills: {len(profile.skills)}")
        console.print(f"  Experience: {profile.total_experience_years}y")
        console.print(f"  Target roles: {', '.join(profile.past_roles)}")
    else:
        console.print("[yellow]No cached profile found[/]")

    output_dir = Path("output")
    if output_dir.exists():
        csv_files = list(output_dir.glob("shortlist_*.csv"))
        if csv_files:
            console.print(f"\n[yellow]CSV exports ({len(csv_files)}):[/]")
            for f in sorted(csv_files, reverse=True)[:5]:
                console.print(f"  - {f.name}")
        else:
            console.print("\n[yellow]No CSV exports yet[/]")


@cli.command()
def clean():
    """Clear all cached data (profile cache, resume hash)."""
    console.print(
        Panel("[bold yellow]Clearing cache files...[/]", border_style="yellow")
    )

    data_dir = Path("data")
    files_removed = []

    cache_files = [
        data_dir / "profile_cache.json",
        data_dir / "resume_hash.txt",
    ]

    for f in cache_files:
        if f.exists():
            f.unlink()
            files_removed.append(f.name)

    if files_removed:
        console.print(f"[green]Removed {len(files_removed)} cache file(s):[/]")
        for name in files_removed:
            console.print(f"  - {name}")
    else:
        console.print("[dim]No cache files to remove[/]")

    console.print(
        "[green]Cache cleaned! Run 'job-hunter run --force-parse' to re-parse resume.[/]"
    )


@cli.command()
def init():
    """Initialize Job Hunter for the current project."""
    console.print(
        Panel("[bold green]Initializing Job Hunter Agent[/]", border_style="green")
    )

    bootstrap_result = bootstrap_config()

    for path, created in bootstrap_result["created"].items():
        if created:
            console.print(f"[green]Created: {path}[/]")
        else:
            console.print(f"[dim]Exists: {path}[/]")

    console.print("[green]Ready! Edit config files and run:[/]")
    console.print("  [bold]job-hunter run --resume your_resume.pdf[/]")


def main():
    cli()


if __name__ == "__main__":
    main()
