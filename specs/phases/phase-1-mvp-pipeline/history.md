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
