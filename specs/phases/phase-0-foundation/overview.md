# Phase 0 — Foundation & Infrastructure

**Status:** Complete ✅  
**Completed:** 2026-04-04  
**Release:** v0.0.1

---

## Goal

Establish the project skeleton, developer tooling, SDD architecture, and all structural scaffolding so every subsequent phase has a stable, well-instrumented foundation to build upon.

## Scope

This phase covers everything required *before* writing business logic:

- Repository structure and packaging configuration
- Spec-Driven Development (SDD) framework integration
- Core configuration schema (Pydantic models + YAML)
- CLI entry point skeleton (Click + Rich)
- LLM provider abstraction (Groq primary + OpenAI fallback)
- Browser session manager (Playwright)
- LangGraph state schema definition
- Project documentation and vision docs

## Deliverables

| Deliverable | File(s) | Status |
|------------|---------|--------|
| Python package setup | `pyproject.toml`, `src/job_hunter/__init__.py` | ✅ Done |
| Dependency lock | `uv.lock` | ✅ Done |
| Config schema | `src/job_hunter/config.py`, `config/user.yaml` | ✅ Done |
| CLI entry point | `src/job_hunter/cli.py` | ✅ Done |
| LLM provider abstraction | `src/job_hunter/llm/provider.py` | ✅ Done |
| Browser manager | `src/job_hunter/browser.py` | ✅ Done |
| LangGraph state + workflow shell | `src/job_hunter/graph/state.py`, `graph/workflow.py` | ✅ Done |
| SDD spec structure | `specs/` entire directory tree | ✅ Done |
| Vision docs | `specs/vision/project-charter.md`, `principles.md`, `success-criteria.md` | ✅ Done |
| Architecture overview | `specs/architecture/overview.md` | ✅ Done |
| SDD enforcement scripts | `scripts/check-sdd-compliance.sh`, `scripts/pre-commit` | ✅ Done |
| OpenCode integration | `.opencode/` commands, plugins, config | ✅ Done |
| Environment template | `.env.example` | ✅ Done |

## Acceptance Criteria

- [x] `uv run job-hunter init` creates directories and config template without errors  
- [x] `uv run job-hunter status` runs without errors (with or without cached profile)  
- [x] `uv run job-hunter run --help` displays all flags correctly  
- [x] Config YAML loads and validates via Pydantic without throwing  
- [x] LLM provider initialises from `.env` without errors  
- [x] Browser manager can launch Chromium in non-headless mode  
- [x] The complete SDD specs directory structure is in place  
- [x] Pre-commit SDD enforcement hook is installed and functional  

## Exit Criteria

All acceptance criteria met. The project skeleton is running, importable, and ready for Phase 1 business logic implementation.

## Known Issues at Exit

None blocking. BUG-001 (interactive config prompts) was discovered during Phase 1 and backlogged.
