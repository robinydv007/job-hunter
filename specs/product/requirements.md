# Product Requirements

**Project:** Job Hunter AI Agent  
**Market:** Indian job platforms  
**Last Updated:** 2026-04-05  

> **This document is the single source of truth for WHAT the product does.**  
> It is phase-agnostic — features are grouped by readiness, not by implementation iteration.  
> For WHEN things ship, see [`specs/roadmap/roadmap.md`](../roadmap/roadmap.md).  
> For HOW they are built, see [`specs/architecture/overview.md`](../architecture/overview.md).

---

## MVP Success Metric

> Given a resume and a config file, the agent independently finds jobs on Naukri, scores them, and produces a populated CSV — with **zero manual search input** from the user.

---

## Feature Registry

### Phase 1 — MVP (✅ Complete)

---

#### FEAT-001 — Resume Parsing & Profile Extraction

**Status:** ✅ Complete  
**Description:**  
Parse the user's resume once to extract a structured profile. Re-parse only when the resume file changes — not on every run. The structured profile is persisted to disk and consumed by all downstream pipeline steps.

**Extracted fields:**
- Skills and tech stack
- Total years of experience and past roles
- Industry domain
- Location preference
- Salary expectation (if available)
- Target job roles (inferred or explicit)
- Name, email, phone, education, summary

**Acceptance criteria:**
- Profile JSON generated on first run
- Subsequent runs use cached profile without calling the LLM
- Supports `.pdf`, `.docx`, `.txt` resume formats
- All required fields populated or gracefully absent

---

#### FEAT-002 — User Config & Profile

**Status:** ✅ Complete  
**Description:**  
A YAML config file (`config/user.yaml`) holds job-seeker preferences and pre-answered screening questions. On first run, the agent validates the config and prompts for any missing required fields — asking only once and saving answers back.

**Profile fields:**

| Field | Description |
|---|---|
| `name` | Full name |
| `total_experience` | Years of total work experience |
| `preferred_roles` | Target job titles |
| `expected_salary_lpa` | Expected CTC in LPA |
| `notice_period` | Current notice period |
| `preferred_locations` | List of preferred cities |
| `remote_preference` | `remote` / `hybrid` / `onsite` |
| `company_size_preference` | e.g. startup, mid-size, enterprise |
| `industry_preference` | e.g. SaaS, fintech, e-commerce |

**Screening answer fields** (used in Phase 2 auto-apply):

| Field | Description |
|---|---|
| `willing_to_relocate` | Yes / No |
| `comfortable_with_shifts` | Yes / No |
| `current_ctc_lpa` | In LPA |
| `expected_ctc_lpa` | In LPA |
| `notice_period` | e.g. 30 days, immediate |
| `reason_for_change` | Brief text answer |
| `visa_status` | e.g. Citizen, not applicable |
| `remote_work_preference` | Yes / No / Flexible |

**Search config fields:**

| Field | Description |
|---|---|
| `platforms` | Job boards to search (`naukri`, `linkedin`, ...) |
| `salary_min_lpa` | Minimum salary filter |
| `salary_max_lpa` | Maximum salary filter |
| `experience_years` | Experience filter for search queries |
| `max_jobs` | Cap on total jobs returned per run |
| `days_old` | Freshness filter — max age of listings in days |

**Scoring config fields:**

| Field | Default | Description |
|---|---|---|
| `shortlist_threshold` | 60 | Score ≥ this → included in CSV |
| `apply_threshold` | 75 | Score ≥ this → auto-apply (Phase 2) |

**Acceptance criteria:**
- Missing required fields prompt the user once and are saved
- Config schema validated via Pydantic on every run
- Invalid values raise a clear error before the pipeline starts

---

#### FEAT-003 — Job Discovery Engine (Naukri)

**Status:** ✅ Complete  
**Description:**  
Search for relevant jobs on Naukri using signals derived from the user profile: target roles, tech skills, experience level, location, and salary range. Apply a freshness filter so only recent listings are returned. Deduplicate results within the current run and against all previous runs so the same job never appears twice.

**Acceptance criteria:**
- Jobs discovered using role, skill, and location signals from user profile
- Only listings within the configured `days_old` freshness window returned
- Duplicate jobs (within-run and across past runs) removed before scoring

---

#### FEAT-004 — Job Relevance Scoring Engine

**Status:** ✅ Complete  
**Description:**  
Each job in the candidate pool is scored on a 0–100 composite scale using a weighted rubric. Jobs below the shortlist threshold are dropped. Jobs above it are written to CSV with a human-readable explanation.

**Scoring factors:** skills match, experience match, role title match, keyword similarity, salary match, location match.

**Output per job:** composite score (0–100), matched skills list, plain-English explanation of why the job was selected.

**Acceptance criteria:**
- All jobs scored before filtering
- Each result includes a human-readable explanation
- Jobs below `shortlist_threshold` do not appear in CSV

---

#### FEAT-005 — CSV Tracking & Export

**Status:** ✅ Complete  
**Description:**  
All shortlisted jobs are exported to a timestamped CSV file. This file serves as the single source of truth for what the agent found, why it was selected, and (in Phase 2) what happened when it applied.

**MVP CSV schema:**

| Column | Description |
|---|---|
| `job_title` | Title as listed on the job board |
| `company` | Company name |
| `job_board` | Platform where job was found |
| `location` | City / remote flag |
| `work_mode` | Remote / hybrid / onsite |
| `experience_required` | Min–max years as listed |
| `salary_lpa` | Salary range in LPA if disclosed |
| `match_score` | 0–100 composite relevance score |
| `matched_skills` | Skills that aligned with requirements |
| `why_selected` | 1–2 line plain-language reasoning |
| `job_url` | Direct apply URL on job board |
| `posted_date` | Date job was posted |
| `job_description` | Full job description text |
| `apply_status` | `Pending` / `Skipped` / `Applied` / `Failed` / `Already Applied` |
| `data_source` | Source identifier for the run |

**Acceptance criteria:**
- One timestamped CSV per run under `output/`
- All shortlisted jobs written with full schema
- `apply_status` column writable in Phase 2 without schema change

---

#### FEAT-006 — Application Status Tracking

**Status:** ✅ Complete (Pending status only; full tracking in Phase 2)  
**Description:**  
The `apply_status` column reflects the lifecycle of every job the agent processes.

| Status | Meaning |
|---|---|
| `Pending` | Shortlisted, score ≥ apply threshold, not yet attempted |
| `Skipped` | Below apply threshold or excluded by filter |
| `Applied` | Successfully submitted *(Phase 2)* |
| `Failed` | Attempted but encountered an error *(Phase 2)* |
| `Already Applied` | Detected as a duplicate application *(Phase 2)* |

---

### Phase 2 — Auto-Apply & Enrichment (🔲 Planned)

---

#### FEAT-007 — Auto-Apply Engine

**Status:** 🔲 Planned  
**Description:**  
For jobs above the `apply_threshold`, the agent opens the job page, fills and submits the application form, and uploads the resume. The apply step is modular and isolated — it can be disabled without affecting any other part of the pipeline.

**Acceptance criteria:**
- Apply step can be disabled via config without breaking the rest of the pipeline
- Every attempt outcome (success, failure, duplicate) is recorded in `apply_status`
- Failures are never silent — reason always logged

---

#### FEAT-008 — Smart Question Answering

**Status:** 🔲 Planned  
**Description:**  
When a job board presents screening questions during apply, the agent answers them in a consistent, context-aware way.

Answers are sourced from `screening_answers` in config first; the LLM fills in anything not pre-configured, using the resume and profile as context. Answers stay consistent across all applications in a session.

**Common questions handled:** expected salary, notice period, relocation willingness, reason for switching, shift comfort, remote preference.

---

#### FEAT-009 — Company Intelligence

**Status:** 🔲 Planned  
**Description:**  
For each shortlisted job, fetch publicly available company data to help the user evaluate the opportunity before applying.

**Phase 2 CSV additions:**

| Column | Description |
|---|---|
| `company_size` | Employee headcount band |
| `company_founded` | Year founded |
| `glassdoor_rating` | Rating out of 5 |
| `work_culture_summary` | Short summary from reviews |
| `core_business` | What the company does |

---

#### FEAT-010 — Resume Cache Invalidation

**Status:** 🔲 Planned  
**Description:**  
Detect when the user's resume file has changed since the last parse and automatically invalidate the cached profile, triggering a fresh extraction on the next run.

---

#### FEAT-011 — Location Match Scoring

**Status:** 🔲 Planned  
**Description:**  
Enable location as an active scoring factor. Location is currently extracted from job listings but has no effect on the match score — this feature activates it.

---

### Phase 3 — Multi-Platform & Intelligence (🔲 Future)

---

#### FEAT-012 — Multi-Platform Job Search

**Status:** 🔲 Future  
**Description:**  
Extend job discovery beyond Naukri to additional Indian and global platforms. Deduplication spans across platforms so the same role is never scored twice.

**Target platforms:** LinkedIn, Hirist, Instahyre, Foundit, Indeed

---

#### FEAT-013 — Multi-Platform Auto-Apply

**Status:** 🔲 Future  
**Description:**  
Extend the auto-apply engine to LinkedIn, Indeed, and other supported platforms where feasible. Each platform requires its own apply module — isolated from the core pipeline.

---

## Out of Scope (All Phases)

- Resume tailoring or rewriting per job
- Email or push notification alerts
- Dashboard or web UI
- Calendar or interview scheduling integration
- Salary negotiation assistance

---

## Known Gaps & Open Items

| ID | Feature | Gap | Impact |
|----|---------|-----|--------|
| BUG-001 | FEAT-002 | Interactive config prompts not triggered on `run` (only on `init`) | User can run with blank required fields |
| — | FEAT-004 | `LOCATION_WEIGHT = 0.0` — location never factors into score | Location preference has no effect on ranking |
| — | FEAT-003 | `required_skills` extraction is a static keyword heuristic | May miss niche/domain-specific skills in job descriptions |
| — | FEAT-001 | No resume change detection for cache invalidation | Stale profile served if user updates resume |
| — | FEAT-003 | No configurable freshness filter exposed to user | `days_old` defaults not surfaced for per-run override |
| — | FEAT-004 | `.net` / technology prefix false positives in role matching | Irrelevant jobs may pass skill matching |

> Full backlog details: [`specs/backlog/backlog.md`](../backlog/backlog.md)

---

## Key Risks

| Risk | Mitigation |
|------|-----------|
| **Anti-bot protection on job boards** | Browser automation with evasion measures; scraper treated as a fragile, maintainable layer |
| **Apply flow brittleness** | Apply step is isolated and can be disabled without touching the rest of the pipeline |
| **Resume parsing accuracy** | LLM extraction with structured output validation before profile is persisted |
| **Duplicate jobs across runs** | Within-run and cross-run deduplication before scoring |
| **LLM rate limits** | Automatic fallback to a secondary LLM provider on rate limit errors |
