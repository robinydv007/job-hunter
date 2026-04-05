# Phase 1 — Plan: MVP Core Pipeline

## Implementation Approach

Build the six LangGraph pipeline nodes sequentially, each building on the previous node's output. The Phase 0 `workflow.py` shell is wired with real implementations.

### Pipeline: Linear StateGraph

```
load_config → parse_resume → search_jobs → score_jobs → filter_shortlist → export_csv → END
```

All data flows through the shared `JobHunterState` TypedDict — no global state, no side-channel communication.

---

### Module Design

#### 1. Resume Parser (`resume/parser.py` + `resume/schema.py`)

**Strategy:** LLM-first extraction with persistent JSON caching.

```
pdf/docx/txt → extract raw text → LLM structured prompt → JSON → ResumeProfile Pydantic model → persist to data/profile.json
```

- Cache check first — if `data/profile.json` exists, skip LLM call entirely
- Supports `.pdf` (pypdf), `.docx` (python-docx), `.txt`
- LLM output is parsed and validated via Pydantic

**ResumeProfile fields extracted:**
`name`, `email`, `phone`, `skills`, `tech_stack`, `total_experience_years`, `past_roles`, `industry_domain`, `location_preference`, `salary_expectation`, `target_roles`, `education`, `summary`

---

#### 2. Naukri Scraper (`search/naukri.py`)

**Query generation:**
- Top 3 `target_roles` × top 3 `tech_stack` skills → role+skill combos
- Per-location queries for each `preferred_locations` entry
- Capped at 10 unique queries per run

**Scraping:**
- Freshness-filtered URLs: `naukri.com/<keyword>-jobs?dd=<days_old>`
- 7 progressive CSS selector strategies (resilient to DOM changes)
- Extracts: title, company, location, description, salary, experience, posted date, apply URL, skills
- Scrolls up to 3x for lazy-loaded content
- `max_jobs_per_query = 20` cap

**Deduplication:**
- Within-run: MD5 fingerprint of `title|company`
- Cross-run: scans all existing `output/shortlist_*.csv` files; pre-populates `seen` set with `MD5(job_title|company|location)`

---

#### 3. Scoring Engine (`scoring/engine.py`)

**6-factor weighted rubric (0–100 composite):**

| Factor | Weight | Logic |
|--------|--------|-------|
| Skills match | 30% | Profile tech skills vs. job required_skills; fuzzy substring; java ≠ javascript guard |
| Experience match | 20% | User years vs. job range; linear penalty for mismatch |
| Role title match | 20% | Exact → word overlap → keyword match |
| Keywords similarity | 15% | Bag-of-words: profile skills/stack vs. full job text |
| Salary match | 8% | Job min salary vs. expected CTC; partial credit ≥80% |
| Location match | 0% | Intentionally zeroed; to be enabled in Phase 2 |
| Remaining | 7% | Reserved |

**Per-job output:**
- `match_score` (0–100)
- `matched_skills` list
- `why_selected` human-readable bullet
- `apply_status`: `"Pending"` if ≥ `apply_threshold`, else `"Skipped"`

---

#### 4. CSV Export (`export/csv_export.py`)

Output path: `output/shortlist_<YYYYMMDD_HHMMSS>.csv`

**Schema columns:**
`job_title`, `company`, `job_board`, `location`, `work_mode`, `experience_required`, `salary_lpa`, `match_score`, `matched_skills`, `why_selected`, `job_url`, `posted_date`, `job_description`, `apply_status`, `data_source`

---

### Risks Identified

| Risk | Mitigation |
|------|-----------|
| Naukri adds new anti-bot measures | 7 selector strategies + non-headless mode |
| LLM returns malformed JSON for resume | Pydantic validation catches it; user sees clear error |
| Zero jobs above shortlist threshold | Pipeline still exports CSV with all scored jobs for inspection |
| CSS selectors break on Naukri DOM update | This is the primary expected maintenance point in Phase 2 |

## Dependencies

- Phase 0 complete (project skeleton, config, CLI, browser, LLM provider, LangGraph shell)

## Effort

~3 days of implementation + iteration on Naukri scraper resilience.
