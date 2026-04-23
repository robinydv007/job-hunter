# Phase 3.2 — Overview: Config Strategy Revamp

**Status:** Planned  
**Target:** TBD  
**Release:** TBD

---

## Goal

Redesign configuration and generated-data handling so config files are the source of truth, generated resume data is disposable, and init/run can safely bootstrap missing files without overwriting user-managed settings.

---

## Why This Matters

The current config model mixes candidate truth, search strategy, screening answers, and platform behavior in a way that is hard to extend. This phase makes the system clearer and safer:

- config wins over generated data
- missing config files can be created automatically
- existing config files are never overwritten on init/run
- user can leave any field blank and rely on defaults
- search, scoring, apply, screening, and platform-specific behavior can evolve independently

---

## Scope

1. **New Config Contract** — Formalize `config/app.yaml`, `config/user.yaml`, and `config/platform.yaml` as the primary writable inputs.
2. **Source of Truth Rules** — Make config override generated resume data everywhere.
3. **Safe Bootstrap** — On `init` or `run`, generate missing config files and seed them with safe resume-derived values when possible.
4. **No Overwrite Policy** — If a config file already exists, never rewrite it automatically.
5. **Flexible Defaults** — Allow blank values using `null`, `[]`, `{}`, or empty strings as appropriate.
6. **Extensibility** — Provide `custom_requirements` / `custom` hooks across search, scoring, apply, screening, and profile data.

---

## Subphases

### 3.2a — Schema + Bootstrap Foundation
- Freeze final config/data schemas.
- Add config templates and bootstrap helpers.
- Ensure missing config files are created on `init` and `run`.

### 3.2b — Runtime Migration
- Replace old config reads with new layered loaders.
- Update search, scoring, apply, screening, parser, and workflow consumers.
- Ensure platform overrides apply above app defaults.

### 3.2c — Validation + Cleanup
- Add regression and precedence tests.
- Confirm config files are never overwritten.
- Finalize migration notes and docs.

---

## Final Field Contract

### `config/app.yaml`

| Key | Type | Required | Notes |
|-----|------|---------:|-------|
| `search.platforms` | `list[string]` | yes | Example: `["naukri", "linkedin"]` |
| `search.preferred_roles` | `list[string]` | no | Primary target roles |
| `search.role_families` | `list[string]` | no | Example: `["qa", "sdet", "devops"]` |
| `search.preferred_locations` | `list[string]` | no | Empty list means search all locations |
| `search.experience_range.min` | `int \| null` | no | Minimum years |
| `search.experience_range.max` | `int \| null` | no | Maximum years |
| `search.salary_range.min_lpa` | `number \| null` | no | Salary floor |
| `search.salary_range.max_lpa` | `number \| null` | no | Salary ceiling |
| `search.company_size_preference` | `list[string]` | no | Example: `["startup", "mid-size", "large"]` |
| `search.company_type_preference` | `list[string]` | no | Example: `["product", "service", "SaaS"]` |
| `search.industry_preference` | `list[string]` | no | Empty allowed |
| `search.work_mode_filter` | `list[string]` | no | `remote`, `hybrid`, `onsite` |
| `search.job_types` | `list[string]` | no | `full-time`, `contract`, etc. |
| `search.excluded_companies` | `list[string]` | no | Empty allowed |
| `search.excluded_keywords` | `list[string]` | no | Empty allowed |
| `search.included_keywords` | `list[string]` | no | Optional boost words |
| `search.title_exclude_keywords` | `list[string]` | no | Example: `["Java"]` |
| `search.freshness_days` | `int \| null` | no | `null` or `0` means auto/disabled |
| `search.max_jobs` | `int \| null` | no | Total jobs scraping cap |
| `search.max_jobs_per_query` | `int \| null` | no | Scrape cap per query |
| `search.custom_requirements` | `list[string]` | no | Generic search constraints |
| `scoring.thresholds.shortlist` | `int` | yes | Shortlist cutoff |
| `scoring.thresholds.apply` | `int` | yes | Apply cutoff |
| `scoring.weights.skills` | `number` | yes | Default weight |
| `scoring.weights.role` | `number` | yes | Default weight |
| `scoring.weights.experience` | `number` | yes | Default weight |
| `scoring.weights.company` | `number` | yes | Default weight |
| `scoring.weights.location` | `number` | yes | Default weight |
| `scoring.weights.work_mode` | `number` | yes | Default weight |
| `scoring.llm_scoring.enabled` | `bool` | no | Optional LLM scorer |
| `scoring.llm_scoring.batch_size` | `int \| null` | no | Nullable |
| `scoring.llm_scoring.shortlist_threshold` | `int \| null` | no | Optional override |
| `scoring.llm_scoring.apply_threshold` | `int \| null` | no | Optional override |
| `scoring.llm_scoring.custom_requirements` | `list[string]` | no | LLM scoring hints |
| `auto_apply.enabled` | `bool` | yes | Auto-apply on/off |
| `auto_apply.max_per_day` | `int \| null` | no | `null` means no explicit cap |
| `auto_apply.max_per_run` | `int \| null` | no | `null` means no explicit cap |
| `auto_apply.delay_between_seconds` | `number \| null` | no | `null` if default delay |
| `auto_apply.require_confirmation` | `bool \| null` | no | `null` if default |
| `auto_apply.skip_if_already_applied` | `bool \| null` | no | Optional |
| `auto_apply.custom_requirements` | `list[string]` | no | Apply constraints |
| `screening.policy.enabled` | `bool` | no | Whether to use screening support |
| `screening.policy.batch_size` | `int \| null` | no | Optional |
| `screening.policy.custom_requirements` | `list[string]` | no | Answer generation constraints |

### `config/user.yaml`

| Key | Type | Required | Notes |
|-----|------|---------:|-------|
| `profile.name` | `string \| null` | no | User name |
| `profile.email` | `string \| null` | no | Contact |
| `profile.phone` | `string \| null` | no | Contact |
| `profile.current_location` | `string \| null` | no | Current city |
| `profile.notice_period_days` | `int \| null` | no | Better than free text |
| `profile.serving_notice_period` | `bool \| null` | no | Optional |
| `profile.currently_working` | `bool \| null` | no | Optional |
| `profile.current_company` | `string \| null` | no | Optional |
| `profile.current_designation` | `string \| null` | no | Optional |
| `profile.current_ctc_lpa` | `number \| null` | no | Optional |
| `profile.previous_company` | `string \| null` | no | Optional |
| `profile.previous_designation` | `string \| null` | no | Optional |
| `profile.previous_ctc_lpa` | `number \| null` | no | Optional |
| `profile.last_working_day` | `string \| null` | no | ISO date string |
| `profile.pan_number` | `string \| null` | no | Optional |
| `profile.alternate_email` | `string \| null` | no | Optional |
| `profile.additional_info` | `map[string, any]` | no | Free-form extra facts |
| `profile.custom_requirements` | `list[string]` | no | Personal constraints |
| `experience.total_experience_years` | `int \| null` | no | User-corrected total experience |
| `experience.skills_with_experience` | `map[string, number]` | no | Skill → years |
| `experience.aliases` | `map[string, list[string]]` | no | Synonyms for normalization |
| `experience.primary_stack` | `list[string]` | no | Main stack |
| `experience.secondary_stack` | `list[string]` | no | Secondary stack |
| `experience.domain_experience` | `map[string, number]` | no | Example: QA: 7, Fintech: 3 |
| `experience.achievements` | `list[string]` | no | User-owned highlights |
| `narrative.career_goal` | `string \| null` | no | Personal story |
| `narrative.strengths` | `string \| null` | no | Personal story |
| `narrative.what_i_bring` | `string \| null` | no | Personal story |
| `narrative.reason_for_change` | `string \| null` | no | Personal story |
| `narrative.preferred_company_type` | `list[string]` | no | Example: `["product", "SaaS"]` |
| `narrative.preferred_work_style` | `string \| null` | no | Example: hands-on, leadership, IC |
| `narrative.custom` | `map[string, any]` | no | Anything user wants |
| `screening_answers.enabled` | `bool` | no | Optional |
| `screening_answers.defaults.current_ctc_lpa` | `number \| null` | no | Optional |
| `screening_answers.defaults.expected_ctc_lpa` | `number \| null` | no | Optional |
| `screening_answers.defaults.notice_period` | `string \| null` | no | Optional |
| `screening_answers.defaults.reason_for_change` | `string \| null` | no | Optional |
| `screening_answers.defaults.visa_status` | `string \| null` | no | Optional |
| `screening_answers.defaults.remote_work_preference` | `string \| null` | no | Optional |
| `screening_answers.defaults.willing_to_relocate` | `bool \| null` | no | Optional |
| `screening_answers.defaults.comfortable_with_shifts` | `bool \| null` | no | Optional |
| `screening_answers.defaults.work_authorization` | `string \| null` | no | Optional |
| `screening_answers.defaults.background_check_consent` | `bool \| null` | no | Optional |
| `screening_answers.defaults.references_available` | `bool \| null` | no | Optional |
| `screening_answers.answers` | `map[string, any]` | no | Free-form screening answers |
| `screening_answers.role_specific` | `map[string, map[string, any]>` | no | Per-role answer sets |
| `screening_answers.custom_requirements` | `list[string]` | no | Answer style constraints |
| `screening_answers.custom_answers` | `map[string, any]` | no | Any extra QA fields |

### `config/platform.yaml`

| Key | Type | Required | Notes |
|-----|------|---------:|-------|
| `naukri.enabled` | `bool` | no | Optional |
| `naukri.login_required` | `bool` | no | Optional |
| `naukri.headless` | `bool` | no | Optional |
| `naukri.page_timeout` | `int \| null` | no | Optional |
| `naukri.max_pages` | `int \| null` | no | Optional |
| `naukri.delay_between_pages` | `number \| null` | no | Optional |
| `naukri.search.max_jobs_per_query` | `int \| null` | no | Optional |
| `naukri.search.query_template` | `string \| null` | no | Optional |
| `naukri.search.param_mapping` | `map[string, string]` | no | Optional |
| `naukri.apply.enabled` | `bool \| null` | no | Optional |
| `naukri.apply.form_style` | `string \| null` | no | Optional |
| `naukri.apply.require_confirmation` | `bool \| null` | no | Optional |
| `naukri.apply.custom_requirements` | `list[string]` | no | Optional |
| `naukri.custom_requirements` | `list[string]` | no | Platform-specific rules |
| `linkedin.enabled` | `bool \| null` | no | Future support |
| `linkedin.search` | `object` | no | Same pattern as Naukri |
| `linkedin.apply` | `object` | no | Same pattern as Naukri |
| `linkedin.custom_requirements` | `list[string]` | no | Optional |

### `data/profile_cache.json`

| Key | Type | Notes |
|-----|------|------|
| `name` | `string` | Parsed from resume |
| `email` | `string` | Parsed from resume |
| `phone` | `string` | Parsed from resume |
| `skills` | `list[string]` | LLM extracted |
| `tech_stack` | `list[string]` | LLM extracted |
| `total_experience_years` | `int` | LLM extracted |
| `past_roles` | `list[string]` | LLM extracted |
| `industry_domain` | `string` | LLM extracted |
| `location_preference` | `string` | LLM extracted |
| `salary_expectation` | `string \| null` | Parsed if present |
| `target_roles` | `list[string]` | LLM inferred |
| `education` | `list[string]` | Parsed |
| `summary` | `string` | LLM generated |
| `detailed.tech_experience` | `map[string, number]` | Technology → years |
| `detailed.achievements` | `list[string]` | LLM extracted |
| `detailed.challenges_solved` | `list[string]` | LLM extracted |
| `detailed.interests` | `list[string]` | LLM extracted |
| `detailed.key_responsibilities` | `list[string]` | LLM extracted |
| `detailed.certifications` | `list[string]` | Optional future field |
| `detailed.domains` | `list[string]` | Optional future field |

---

## Code Impact Map

| Area | Likely Changes |
|------|----------------|
| `src/job_hunter/config/__init__.py` | Define final config models, layered loaders, merge precedence, bootstrap helpers |
| `src/job_hunter/cli.py` | Generate missing config files on `init` and `run`; stop overwriting existing files |
| `src/job_hunter/resume/parser.py` | Seed `user.yaml` when missing; keep `profile_cache.json` generated-only; merge config/user truth into runtime profile |
| `src/job_hunter/graph/nodes.py` | Consume new effective config object and user truth; remove assumptions about current `profile`/`screening` layout |
| `src/job_hunter/search/naukri.py` | Read search defaults from `app.yaml` and platform overrides; preserve all-location behavior when preferred list is empty |
| `src/job_hunter/scoring/engine.py` | Replace direct reads of old config fields with new schema; support role families and custom requirements |
| `src/job_hunter/scoring/llm_scorer.py` | Build prompts from new user/app config layout; add new fields and custom requirements |
| `src/job_hunter/apply/naukri_apply.py` | Read screening policy and answers from new locations; use user truth and platform behavior together |
| `src/job_hunter/export/csv_export.py` | Review if CSV rows need additional columns derived from new config-driven fields; otherwise keep output stable |
| `src/job_hunter/graph/workflow.py` | Ensure pipeline uses the new config bootstrap and effective config model |
| `src/job_hunter/resume/schema.py` | Align extracted resume schema with new cache contract if needed |


---

## Proposed File Model

| File | Purpose | Mutable By User | Generated |
|------|---------|-----------------|-----------|
| `config/app.yaml` | Search, scoring, apply, screening policy, platform-agnostic strategy | Yes | No |
| `config/user.yaml` | Candidate truth, corrections, narrative, screening answers, custom facts | Yes | Seeded only when missing |
| `config/platform.yaml` | Platform-specific behavior and overrides | Yes | No |
| `data/profile_cache.json` | Resume-extracted facts and detailed profile | No | Yes |

---

## Bootstrap Rules

1. If `config/app.yaml` is missing, create it from a template.
2. If `config/user.yaml` is missing, create it and seed safe fields from resume data when available.
3. If `config/platform.yaml` is missing, create it from a template.
4. If a file already exists, leave it unchanged.
5. Resume parsing may update `data/profile_cache.json`, but never user config.

---

## Runtime Precedence

1. `config/platform.yaml` overrides platform-specific defaults.
2. `config/app.yaml` provides global strategy defaults.
3. `config/user.yaml` provides candidate truth and user-entered answers.
4. `data/profile_cache.json` provides generated resume facts.
5. Code defaults are the final fallback.

---

## Success Criteria

- Missing config files are generated on `init` or `run`.
- Existing config files are not overwritten.
- Resume-derived bootstrap data only fills empty/missing fields.
- Config values take priority over generated data.
- Empty values are supported intentionally across all config sections.
- Search, scoring, apply, and screening can use custom requirements per section.
