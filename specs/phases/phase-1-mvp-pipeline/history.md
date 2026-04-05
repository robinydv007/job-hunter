# Phase 1 — History Log

> Append-only log. Never edit existing entries. Format: [TYPE] YYYY-MM-DD — Short title

---

[FEATURE] 2026-04-05 — Resume parser with LLM extraction and JSON caching
Topics: resume, llm, caching
Affects-phases: none
Affects-docs: specs/architecture/overview.md#resume-parser
Detail: Implemented LLM-first resume parsing using Groq (with OpenAI fallback). Profile is persisted to data/profile.json after first extraction. Subsequent runs skip the LLM call entirely. Supports PDF, DOCX, and TXT resume formats.

[FEATURE] 2026-04-05 — Naukri Playwright scraper with resilient selector strategies
Topics: naukri, playwright, scraping, deduplication
Affects-phases: none
Affects-docs: specs/architecture/overview.md#naukri-scraper
Detail: Built NaukriScraper with 7 progressive CSS selector strategies to handle DOM variability. Added within-run deduplication (MD5 of title|company) and cross-run deduplication (scan output/*.csv). Query generation combines target_roles × tech_stack × preferred_locations, capped at 10 queries.

[FEATURE] 2026-04-05 — 6-factor weighted scoring engine
Topics: scoring, rubric, matching
Affects-phases: none
Affects-docs: specs/architecture/overview.md#scoring-engine
Detail: Implemented composite 0-100 score from: skills match (30%), experience match (20%), role title match (20%), keywords similarity (15%), salary match (8%), location match (0%). Each job also gets matched_skills list, why_selected summary, and apply_status field.

[DECISION] 2026-04-05 — Location weight intentionally set to 0.0
Topics: scoring, location, work-mode
Affects-phases: phase-2-auto-apply
Affects-docs: specs/architecture/overview.md#known-gaps
Detail: LOCATION_WEIGHT was set to 0.0 because remote/hybrid job listings often omit location data or use generic strings. Factoring it in caused false negatives for good jobs. This will be revisited for Phase 2 when work_mode data is more reliable from the scraper.

[FEATURE] 2026-04-05 — CSV export with full 15-column MVP schema
Topics: csv, export, schema
Affects-phases: none
Affects-docs: specs/architecture/overview.md#csv-export
Detail: Implemented timestamped CSV export to output/shortlist_<YYYYMMDD_HHMMSS>.csv. All 15 schema columns populated: job_title, company, job_board, location, work_mode, experience_required, salary_lpa, match_score, matched_skills, why_selected, job_url, posted_date, job_description, apply_status, data_source.

[DISCOVERY] 2026-04-05 — BUG-001: Interactive config prompts missing on `run` command
Topics: config, ux, validation
Affects-phases: phase-1-mvp-pipeline
Affects-docs: specs/backlog/backlog.md, specs/backlog/details/BUG-001.md
Detail: The load_config node validates the config but does not interactively prompt for missing required fields during `run`. The `init` command creates a template, but if a user skips filling it in, the pipeline runs with defaults silently. This violates the "User In Control" principle from specs/vision/principles.md.

[DISCOVERY] 2026-04-05 — No resume change detection for cache invalidation
Topics: resume, caching, tech-debt
Affects-phases: phase-2-auto-apply
Affects-docs: specs/architecture/overview.md#known-gaps
Detail: The resume parser checks if data/profile.json exists and uses it — it does not detect if resume.pdf has been modified. Users who update their resume must manually delete data/profile.json to force re-parsing. A file hash check would fix this automatically.

[NOTE] 2026-04-05 — Phase 1 MVP pipeline validated end-to-end
Topics: validation, mvp
Affects-phases: none
Affects-docs: specs/vision/success-criteria.md
Detail: Full run of `job-hunter run --resume resume.pdf` completed successfully. Resume parsed, Naukri scraped 30+ jobs, scoring produced valid scores, shortlist filtered and CSV exported to output/. The MVP success metric from success-criteria.md is met.

[FEATURE] 2026-04-05 — ENH-003: Expand config for search params, auto-apply controls, screening answers
Topics: config, search, auto-apply, screening
Affects-phases: phase-2-auto-apply
Affects-docs: specs/backlog/details/ENH-003.md, config/user.yaml
Detail: Added work_mode_filter, job_types, excluded_companies, excluded_keywords to SearchConfig. Created AutoApplyConfig with rate limiting and safety controls. Added 10 new fields to ScreeningAnswers (current_employer, current_designation, etc.). Wired exclusion filters into search_jobs_node for post-scrape filtering.

[FEATURE] 2026-04-05 — ENH-004: Smart job freshness filter with auto-calculation
Topics: freshness, run-history, search
Affects-phases: none
Affects-docs: specs/backlog/details/ENH-004.md, config/user.yaml
Detail: Added freshness field to SearchConfig (0=auto, 1/3/7/15/30=days). Implemented resolve_freshness() that auto-calculates from last run history in data/run_history.json. First run defaults to dd=7. Run history is recorded after each search with timestamp, freshness_used, jobs_found, platform.

[FEATURE] 2026-04-05 — ENH-005: Overhaul search query generation
Topics: search, queries, scraping, limits
Affects-phases: none
Affects-docs: specs/backlog/details/ENH-005.md, config/user.yaml
Detail: Rewrote _build_search_queries to use role-only (no skills), removed arbitrary 10-query cap. Added max_roles (default 5) and max_locations (default 3) config fields. Set 100 raw jobs per query soft limit (internal). Removed 150 total job cap. Added max_jobs config controls final CSV output (0=all qualified). Added random 3-8s delay between queries.

[FEATURE] 2026-04-05 — ENH-006: Anti-blocking randomize timing
Topics: anti-blocking, timing, jitter, stealth
Affects-phases: none
Affects-docs: specs/backlog/details/ENH-006.md, config/user.yaml
Detail: All fixed sleeps replaced with random.uniform() jitter. Post-load 2-5s, between scrolls 1.5-3s, scroll count 2-4, scroll distance 400-800px. Between-queries delay configurable via delay_min_seconds/delay_max_seconds in SearchConfig.

[ARCH_CHANGE] 2026-04-05 — TD-004: Prune unused fields from JobHunterState
Topics: state, cleanup, tech-debt
Affects-phases: none
Affects-docs: specs/backlog/details/TD-004.md
Detail: Removed profile_validated (never read), messages (LangGraph add_messages overhead, not a conversational agent), errors (replaced with RuntimeError exceptions that properly stop the graph). JobHunterState now has 8 fields instead of 11.

[DISCOVERY] 2026-04-05 — Post-ENH-005 regression: skill match=0, scores dropped 62→31
Topics: scoring, skills, freshness, regression
Affects-phases: none
Affects-docs: specs/backlog/backlog.md
Detail: ENH-005 role-only queries caused broader job results. Combined with hardcoded ~40-keyword skill extraction, this produced 0% skill matches. Scores dropped from 62-76 to 31-45. Freshness dd param only sorts, doesn't filter — older jobs appeared. Fixed by: (1) using jobAge=N in Naukri URL for actual filtering, (2) extracting skills from div.row5 on listing page, (3) fallback to scanning description for user's own skills via word-boundary regex, (4) restored threshold to 60.

[FEATURE] 2026-04-05 — Resume caching with --force-parse override
Topics: resume, caching, cli, performance
Affects-phases: none
Affects-docs: specs/architecture/overview.md#resume-parser
Detail: Added automatic resume caching — if data/profile.json exists and --resume is not explicitly passed, the pipeline skips LLM parsing entirely. New --force-parse CLI flag allows users to override cache and force re-parsing. Cached profile detection runs in cli.py before pipeline start.

[FEATURE] 2026-04-05 — Search role priority: user.yaml preferred_roles over parsed target_roles
Topics: search, config, roles, priority
Affects-phases: none
Affects-docs: specs/architecture/overview.md#search-jobs
Detail: search_jobs_node now checks config.profile.preferred_roles first. If set, it overrides profile.target_roles from parsed resume. Rationale: user.yaml is explicit intent; profile.json is LLM-inferred. Console output indicates which source was used.

[FEATURE] 2026-04-05 — Title tech penalty in scoring engine
Topics: scoring, title, tech-stack, penalty
Affects-phases: none
Affects-docs: specs/architecture/overview.md#scoring-engine
Detail: Added _check_title_tech_penalty() that scans job titles for primary tech keywords (Java, Python, .NET, SAP, etc.). If the job title names a tech the user lacks, the composite score is halved (0.5x multiplier). Prevents mismatched roles like "Java Technical Lead" from scoring high for non-Java developers. Penalty is noted in why_selected explanation.
