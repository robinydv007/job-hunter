# Phase 0 — Retrospective: Foundation & Infrastructure

**Completed:** 2026-04-04  
**Release:** v0.0.1

---

## What Went Well

- **UV + Pydantic v2 combo** — Zero friction on dependency management and config validation; Pydantic's error messages caught config mistakes immediately during testing.
- **SDD framework from the start** — Having specs/, backlog/, and decision-tracking pre-installed means every future agent run has full context.
- **Click + Rich CLI** — Clean terminal output and `--help` discoverability required almost no extra code.
- **LLM provider abstraction** — The fallback mechanism (Groq → OpenAI) worked as designed; no pipeline failures due to rate limits during Phase 1 testing.

## What Could Have Been Better

- **SDD applied retroactively** — Ideally, the SDD architecture is adopted *before* any code is written. Phase 0 and Phase 1 docs were both written after the implementation was already complete. Future projects should create the phase docs *first*.
- **No changelog directory created** — The `specs/README.md` references `specs/changelog/` but it was not created during this phase. It should be added at the start of Phase 1.

## Lessons Learned

1. For greenfield projects: write `overview.md` and `plan.md` *before* a single line of code.
2. The pre-commit SDD enforcement is powerful — installing it in Phase 0 prevents doc drift from the very first commit.
3. `non-headless` Playwright should always be the default for scraping jobs that use bot detection.

## Metrics

| Metric | Value |
|--------|-------|
| Duration | ~2 days |
| Commits | ~8 (including SDD setup commits) |
| Modules created | 6 (cli, config, browser, llm/provider, graph/state, graph/workflow) |
| Test coverage | 0% (no tests written in Phase 0) |

## Phase 1 Handoff Notes

- All imports are verified working; the project is installable via `uv sync`
- The LangGraph workflow shell in `graph/workflow.py` is ready to receive real node implementations
- Config YAML template is at `config/user.yaml`; user must fill in Naukri credentials in `.env`
- Open bug: BUG-001 (interactive config prompts missing) — discovered mid–Phase 1, captured in backlog
