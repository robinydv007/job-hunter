# Success Criteria

> **MVP Success Metric:** Given a resume and config, the agent independently finds jobs on Naukri, scores them, and produces a populated CSV — with zero manual search input from the user.
>
> ✅ **MVP Success Metric ACHIEVED** — 2026-04-05 (Phase 1 complete)

## Phase 0 — Foundation & Infrastructure
* [x] Python package installable via UV (`uv sync`)
* [x] CLI commands (`init`, `run`, `status`) functional with `--help` output
* [x] Config YAML loads and validates via Pydantic
* [x] SDD spec structure in place with enforcement hooks
* [x] LLM provider initialises and switches between Groq and OpenAI

## Phase 1 — MVP
* [x] Resume parsing and structured profile extraction (with LLM + caching)
* [x] Config file loading and missing-field detection (prompt-on-run pending BUG-001)
* [x] Job search on Naukri (Playwright-based, multi-query, lazy-load support)
* [x] Within-run deduplication (title|company fingerprint)
* [x] Cross-run deduplication (scan past CSV exports)
* [x] Relevance scoring with 6-factor weighted rubric (0–100 composite)
* [x] CSV export with full 15-column schema and apply status tracking

## Phase 2 — Apply & Enrichment
* [ ] Fix BUG-001: Interactive config prompts on `run` command
* [ ] Auto-apply to jobs above the configured score threshold
* [ ] Smart question answering from config `screening_answers` and resume context
* [ ] Apply status written back to CSV (`Applied` / `Failed` / `Already Applied`)
* [ ] Location match scoring enabled (weight > 0)
* [ ] Resume change detection for cache invalidation
* [ ] Unit test coverage for scoring engine, parser, scraper
* [ ] Multi-platform support: LinkedIn, Indeed, Hirist, Instahyre, Foundit
* [ ] Company intelligence enrichment columns (`company_size`, `glassdoor_rating`, `core_business`)
