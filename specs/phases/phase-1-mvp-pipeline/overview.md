# Phase 1 — MVP Core Pipeline

**Status:** Complete ✅  
**Completed:** 2026-04-05  
**Release:** v0.1.0

---

## Goal

Build and validate the full end-to-end MVP pipeline: given a resume and config, the agent independently discovers jobs on Naukri, scores them against the user's profile, and exports a structured ranked CSV — with zero manual search input.

## Scope

This phase implements all six LangGraph pipeline nodes and their supporting modules:

| Node | Module | Responsibility |
|------|--------|---------------|
| `load_config` | `config.py` | Validate + prompt for missing config fields |
| `parse_resume` | `resume/parser.py`, `resume/schema.py` | LLM-based resume extraction with caching |
| `search_jobs` | `search/naukri.py` | Playwright-based Naukri DOM scraper |
| `score_jobs` | `scoring/engine.py` | 6-factor weighted rubric scoring |
| `filter_shortlist` | `graph/nodes.py` | Threshold filter + top-N sort |
| `export_csv` | `export/csv_export.py` | CSV writer with full MVP schema |

## Deliverables

| Deliverable | File(s) | Status |
|------------|---------|--------|
| Resume parser + caching | `src/job_hunter/resume/parser.py`, `resume/schema.py` | ✅ Done |
| Naukri scraper | `src/job_hunter/search/naukri.py` | ✅ Done |
| Scoring engine | `src/job_hunter/scoring/engine.py` | ✅ Done |
| CSV export | `src/job_hunter/export/csv_export.py` | ✅ Done |
| LangGraph node implementations | `src/job_hunter/graph/nodes.py` | ✅ Done |
| Full workflow wired | `src/job_hunter/graph/workflow.py` | ✅ Done |
| Profile JSON caching | `data/profile.json` (created at runtime) | ✅ Done |
| Cross-run deduplication | Implemented in `search/naukri.py` | ✅ Done |
| Architecture documentation | `specs/architecture/overview.md` | ✅ Done |

## Acceptance Criteria

- [x] `job-hunter run` completes without unhandled exceptions given valid resume and config
- [x] Resume is parsed (or loaded from cache) and produces a valid `ResumeProfile` object
- [x] Naukri scraper finds ≥ 1 job per search query without manual intervention
- [x] All scraped jobs receive a composite match score between 0 and 100
- [x] At least 1 job appears in the shortlist output (above threshold)
- [x] A timestamped CSV is written to `output/shortlist_YYYYMMDD_HHMMSS.csv`
- [x] CSV contains all required schema columns: `job_title`, `company`, `match_score`, `matched_skills`, `why_selected`, `job_url`, `apply_status`, etc.
- [x] Within-run deduplication prevents the same job from appearing twice in one run
- [x] Cross-run deduplication prevents jobs from past CSV exports reappearing

## Exit Criteria

A complete run from `job-hunter run` produces a populated, correctly-structured CSV shortlist with no script crashes. The MVP success metric from `specs/vision/success-criteria.md` is met.

## Known Issues at Exit

| ID | Description | Severity | Backlog Ref |
|----|-------------|----------|-------------|
| BUG-001 | Interactive config prompts not triggered on `run` | P1 | `specs/backlog/details/BUG-001.md` |
| — | `LOCATION_WEIGHT = 0.0` in scoring engine | Low | Noted in architecture overview |
| — | No resume change detection for cache invalidation | Low | Phase 2 candidate |
| — | `required_skills` extraction uses static keyword list | Low | Phase 2 candidate |
