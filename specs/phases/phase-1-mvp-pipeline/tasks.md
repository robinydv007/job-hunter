# Phase 1 — Tasks: MVP Core Pipeline

> **Status: COMPLETE** ✅ — All tasks finished 2026-04-05

## Task Checklist

### 1. Resume Module
- [x] Create `ResumeProfile` Pydantic model in `resume/schema.py`
  - Fields: `name`, `email`, `phone`, `skills`, `tech_stack`, `total_experience_years`, `past_roles`, `industry_domain`, `location_preference`, `salary_expectation`, `target_roles`, `education`, `summary`
- [x] Implement `parse_resume(resume_path)` in `resume/parser.py`
  - PDF extraction via `pypdf`
  - DOCX extraction via `python-docx`
  - Plain text passthrough
- [x] Implement LLM-based structured extraction with prompt
- [x] Implement JSON → Pydantic model parsing
- [x] Implement cache load/save: `data/profile.json`
- [x] Export `load_profile()` function for `job-hunter status` command
- [x] Verify: run with `resume.pdf` → produces valid `ResumeProfile`
- [x] Verify: second run reads from cache (no LLM call)

### 2. Naukri Scraper
- [x] Implement `NaukriScraper` class in `search/naukri.py`
- [x] Implement search query generation (roles × skills × locations, max 10)
- [x] Construct freshness-filtered Naukri URLs (`?dd=<days_old>`)
- [x] Implement 7 progressive CSS selector strategies for job cards
- [x] Extract job fields: title, company, location, description, salary, experience, posted date, URL, skills
- [x] Implement scroll-to-load (max 3 scrolls per page)
- [x] Implement within-run deduplication (MD5 of `title|company`)
- [x] Implement cross-run deduplication (scan `output/*.csv` at startup)
- [x] Cap results at `max_jobs_per_query` per query (default: 20)
- [x] Verify: scraper returns ≥ 1 job for a test query without crashing

### 3. Scoring Engine
- [x] Implement `ScoredJob` dataclass / model in `scoring/engine.py`
- [x] Implement 6-factor weighted rubric:
  - [x] Skills match (30%) with fuzzy matching + false-positive guard
  - [x] Experience match (20%) with linear penalty
  - [x] Role title match (20%)
  - [x] Keywords similarity (15%) via bag-of-words
  - [x] Salary match (8%)
  - [x] Location match (0% — intentionally zeroed)
- [x] Generate `matched_skills` list per job
- [x] Generate `why_selected` human-readable summary per job
- [x] Set `apply_status` based on `apply_threshold`
- [x] Verify: each job receives a score in [0, 100]

### 4. CSV Export
- [x] Implement `export_to_csv(jobs, path)` in `export/csv_export.py`
- [x] Write all 15 MVP schema columns
- [x] Generate timestamped output filename: `output/shortlist_<YYYYMMDD_HHMMSS>.csv`
- [x] Verify: CSV opens in spreadsheet with correct column headers

### 5. LangGraph Wiring
- [x] Implement `load_config_node` in `graph/nodes.py`
- [x] Implement `parse_resume_node` in `graph/nodes.py`
- [x] Implement `search_jobs_node` in `graph/nodes.py`
- [x] Implement `score_jobs_node` in `graph/nodes.py`
- [x] Implement `filter_shortlist_node` in `graph/nodes.py`
- [x] Implement `export_csv_node` in `graph/nodes.py`
- [x] Wire all nodes into `StateGraph` in `workflow.py`
- [x] Set entry point and END edge
- [x] Verify: `build_workflow().invoke(initial_state)` completes without error

### 6. End-to-End Validation
- [x] Full pipeline run: `job-hunter run --resume resume.pdf`
- [x] Confirm CSV created in `output/` directory
- [x] Confirm CSV contains shortlisted jobs with all schema columns populated
- [x] Confirm cross-run deduplication works on second run (no duplicate jobs)
- [x] Confirm `job-hunter status` shows cache and CSV history correctly

### 7. Documentation
- [x] Write `specs/architecture/overview.md` (full system architecture)
- [x] Update `specs/vision/success-criteria.md` — mark Phase 1 criteria complete
- [x] Create `specs/backlog/details/BUG-001.md` — document missing interactive prompts bug

## Known Issues Discovered During This Phase

- **BUG-001**: Interactive config prompts not triggered on `run` command (only `init`). Logged in backlog. Does not block MVP but violates "User In Control" principle.
- **LOCATION_WEIGHT = 0.0**: Location is intentionally zeroed in scoring engine pending future evaluation. Noted in architecture doc.
