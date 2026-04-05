# Job Hunter Agent — Product Requirements

**Version:** v0.2 — Draft  
**Market:** Indian job platforms  
**Status:** In progress

---

## Purpose

An agentic AI system that reads a user's resume, discovers relevant jobs on Indian job platforms, evaluates each listing for fit, and exports a structured shortlist — with the ability to auto-apply in a later phase. The system minimises manual effort while keeping the user in control and maintaining full transparency over every decision made.

> **MVP success metric:** Given a resume and config, the agent independently finds jobs on Naukri, scores them, and produces a populated CSV — with zero manual search input from the user.

---

## Core Features

### 1. Resume Understanding `MVP`

Parse the resume once to extract a structured profile. Re-parse only when the resume file changes — not on every run.

Extracted fields:

- Skills and tech stack
- Total years of experience and past roles
- Industry domain
- Location preference
- Salary expectation (if available)
- Target job roles (inferred or explicit)

The structured profile is stored and consumed by all downstream steps.

### 2. User Config & Profile `MVP`

A config file holds job seeker preferences and pre-answered screening questions. On first run, the agent validates the config and prompts for any missing required fields — asking only once.

**Profile fields:**

| Field | Description |
|---|---|
| `name` | Full name |
| `total_experience` | Years of total work experience |
| `preferred_roles` | Target job titles |
| `expected_salary` | Expected CTC in LPA |
| `notice_period` | Current notice period |
| `preferred_locations` | List of preferred cities |
| `remote_preference` | Remote / hybrid / onsite |
| `company_size_preference` | e.g. startup, mid-size, enterprise |
| `industry_preference` | e.g. SaaS, fintech, e-commerce |

**Screening answer fields** (used during auto-apply in Phase 2):

| Field | Description |
|---|---|
| `willing_to_relocate` | Yes / No |
| `comfortable_with_shifts` | Yes / No |
| `expected_ctc` | In LPA |
| `current_ctc` | In LPA |
| `notice_period` | e.g. 30 days, immediate |
| `reason_for_change` | Brief text answer |
| `visa_status` | e.g. Citizen, not applicable |
| `remote_work_preference` | Yes / No / Flexible |

**Config schema reference:**

```yaml
profile:
  name: ""
  total_experience: 0               # years
  preferred_roles: []
  expected_salary_lpa: 0
  notice_period: ""
  preferred_locations: []
  remote_preference: hybrid          # remote | hybrid | onsite
  company_size_preference: []        # startup | mid-size | enterprise
  industry_preference: []

search:
  platforms: [naukri]                # naukri | linkedin | hirist | indeed | instahyre | foundit
  salary_min_lpa: 0
  salary_max_lpa: 0
  experience_years: 0

scoring:
  shortlist_threshold: 60            # score >= this → include in CSV
  apply_threshold: 75                # score >= this → auto-apply (Phase 2)

screening_answers:
  willing_to_relocate: false
  comfortable_with_shifts: false
  current_ctc_lpa: 0
  expected_ctc_lpa: 0
  notice_period: ""
  reason_for_change: ""
  visa_status: "not applicable"
  remote_work_preference: "flexible"
```

### 3. Job Discovery Engine `MVP`

Search for relevant jobs using signals derived from the user profile: skills, target roles, experience level, location, and salary range. Paginate through results and collect all listings into a candidate pool before scoring begins.

**MVP platform:** Naukri  
**Phase 2 platforms:** LinkedIn, Indeed, Hirist, Instahyre, Foundit

Cross-platform duplicate detection (Phase 2) uses a fingerprint of job title + company name + location to avoid scoring the same role twice.

### 4. Job Relevance Scoring Engine `MVP`

Each job in the candidate pool is scored on a 0–100 scale using a weighted rubric. Jobs below the shortlist threshold are dropped. Jobs above it are written to CSV with a human-readable explanation.

**Scoring rubric:**

| Factor | Weight |
|---|---|
| Skills match | High |
| Experience match | High |
| Role title match | High |
| Keywords similarity | High |
| Salary match | Medium |
| Location match | Medium |
| Company type fit | Low |

**Scoring output example:**

```
Match Score: 82%

Why Selected:
- 8 of 10 required skills matched
- Experience: role requires 8 yrs, user has 10 yrs
- Role: Technical Lead (matches target)
- Location: Gurgaon (preferred city)
- Salary: within expected range
```

### 5. Company Intelligence `Phase 2`

For each shortlisted job, fetch publicly available company data to help the user evaluate the opportunity before applying.

Fetched fields:

- Company size (headcount band)
- Founded year
- Core business / domain
- Work culture summary
- Employee reviews summary
- Glassdoor rating (if available)

This data is appended as additional columns in the CSV.

### 6. CSV Tracking System `MVP`

All shortlisted jobs are exported to a timestamped CSV file. This file serves as the single source of truth for what the agent found, why it was selected, and what happened when it applied. It is updated in place throughout the agent's run.

**CSV schema:**

| Column | Description | Phase |
|---|---|---|
| `job_title` | Title as listed on the job board | MVP |
| `company` | Company name | MVP |
| `job_board` | Platform where job was found | MVP |
| `location` | City / remote flag | MVP |
| `work_mode` | Remote / hybrid / onsite | MVP |
| `experience_required` | Min–max years as listed | MVP |
| `salary_lpa` | Salary range in LPA if disclosed | MVP |
| `match_score` | 0–100 composite relevance score | MVP |
| `matched_skills` | Skills that aligned with job requirements | MVP |
| `why_selected` | 1–2 line plain-language reasoning | MVP |
| `job_url` | Direct apply URL on job board | MVP |
| `apply_status` | Pending / Applied / Skipped / Failed / Already Applied | MVP |
| `fail_reason` | Error detail if apply attempt failed | Phase 2 |
| `company_size` | Employee headcount band | Phase 2 |
| `company_founded` | Year founded | Phase 2 |
| `glassdoor_rating` | Rating out of 5 | Phase 2 |
| `work_culture_summary` | Short summary from reviews | Phase 2 |
| `core_business` | What the company does | Phase 2 |

### 7. Auto-Apply Engine `Phase 2`

For jobs above the apply threshold, the agent opens the job page, fills and submits the application form, and uploads the resume. The apply step is modular and isolated — it can be disabled without affecting any other part of the pipeline.

Apply flow:

1. Open job listing page
2. Click the apply button
3. Fill application form fields
4. Upload resume
5. Answer any screening questions (see Smart Q&A below)
6. Submit and record outcome

### 8. Smart Question Answering `Phase 2`

When a job board presents screening questions during apply, the agent answers them in a consistent, context-aware way.

Resolution order:

1. Check config screening answers for an exact match
2. If not found, use LLM to infer an appropriate answer from the resume and profile
3. Maintain answer consistency across all applications in a session

Common questions handled: expected salary, notice period, relocation willingness, reason for switching, shift comfort, remote preference.

### 9. Application Status Tracking `MVP`

The `apply_status` column in the CSV reflects the outcome of every job the agent processes:

| Status | Meaning |
|---|---|
| `Pending` | Shortlisted, not yet attempted |
| `Applied` | Successfully submitted |
| `Skipped` | Below apply threshold or excluded |
| `Failed` | Attempted but encountered an error |
| `Already Applied` | Detected as a duplicate application |

---

## Phase Roadmap

### Phase 1 — MVP

- Resume parsing and structured profile extraction
- Config file loading and missing-field prompting
- Job search on Naukri
- Relevance scoring with weighted rubric
- CSV export with full schema and status tracking

### Phase 2 — Apply & Enrichment

- Auto-apply to jobs above the configured threshold
- Smart question answering from config and resume context
- Apply status written back to CSV (Applied / Failed / Already Applied)
- Multi-platform support: LinkedIn, Indeed, Hirist, Instahyre, Foundit
- Company intelligence enrichment columns

---

## Key Risks

### Anti-bot protection on job platforms

Most Indian job platforms use rate-limiting, CAPTCHAs, or bot detection. Plan for human-like delays, browser fingerprint handling, and graceful degradation from the start. Treat the scraper as a fragile layer that will need ongoing maintenance.

### Apply flow brittleness

Application form structures change without notice. The auto-apply step must be isolated so it can be updated or disabled without touching the rest of the pipeline. Failures should be logged, not silent.

### Resume parsing accuracy

Unstructured resume formats (columns, graphics, PDFs with images) can cause extraction errors. Use LLM-based extraction with a strict output schema and a validation step before the profile is persisted.

### Duplicate job detection

The same role can appear across multiple platforms or multiple pages of the same platform. Deduplicate using a fingerprint of job title + company + location before scoring begins.

---

## Out of Scope (MVP)

- Auto-apply (Phase 2)
- Multi-platform search beyond Naukri (Phase 2)
- Company intelligence enrichment (Phase 2)
- Resume tailoring or editing per job
- Email or notification alerts
- Dashboard or web UI
