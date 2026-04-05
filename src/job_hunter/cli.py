"""CLI entry point for Job Hunter Agent."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from job_hunter.config import (
    load_config,
    load_config_dict,
    validate_profile,
    prompt_missing_fields,
    save_config,
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
def run(resume: str | None, config: str | None, headless: bool):
    """Run the full job hunter pipeline."""
    console.print(
        Panel("[bold green]Job Hunter Agent[/] Starting...", border_style="green")
    )

    # Validate raw config and prompt for missing fields BEFORE Pydantic validation
    raw = load_config_dict(config)
    missing = validate_profile(raw)
    if missing:
        console.print(f"[yellow]Missing config fields: {', '.join(missing)}[/]")
        answers = prompt_missing_fields(missing)
        save_config(answers)
        console.print("[green]Config updated and saved.[/]")

    # Load config (now with validated data)
    app_config = load_config(config)

    # Find resume
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

    async def run_pipeline():
        browser = BrowserManager(headless=headless)
        page = await browser.start()

        try:
            # Login to Naukri
            logged_in = await browser.login_naukri()
            if not logged_in:
                console.print("[red]Failed to login to Naukri. Check credentials.[/]")
                await browser.close()
                raise SystemExit(1)

            # Build initial state
            initial_state = {
                "config": app_config,
                "resume_path": resume,
                "profile": None,
                "raw_jobs": [],
                "scored_jobs": [],
                "shortlisted_jobs": [],
                "csv_path": "",
                "browser_page": page,
            }

            # Run workflow
            workflow = build_workflow()
            result = workflow.invoke(initial_state)

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
    from job_hunter.resume.parser import load_profile

    profile = load_profile()
    if profile:
        console.print(f"[green]Cached profile: {profile.name}[/]")
        console.print(f"  Skills: {len(profile.skills)}")
        console.print(f"  Experience: {profile.total_experience_years}y")
        console.print(f"  Target roles: {', '.join(profile.target_roles)}")
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
def init():
    """Initialize Job Hunter for the current project."""
    console.print(
        Panel("[bold green]Initializing Job Hunter Agent[/]", border_style="green")
    )

    config_path = Path("config/user.yaml")
    if config_path.exists():
        console.print(f"[dim]Config already exists: {config_path}[/]")
    else:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        from job_hunter.config import AppConfig
        import yaml

        with open(config_path, "w") as f:
            yaml.dump(
                AppConfig().model_dump(), f, default_flow_style=False, sort_keys=False
            )
        console.print(f"[green]Created config: {config_path}[/]")

    Path("data").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)
    console.print("[green]Ready! Edit config/user.yaml and run:[/]")
    console.print("  [bold]job-hunter run --resume your_resume.pdf[/]")


def main():
    cli()


if __name__ == "__main__":
    main()
