# Phase 3.2 — History: Config Strategy Revamp

> Phase started: 2026-04-23 | Phase completed: 2026-04-23

---

[NOTE] 2026-04-23 — Phase 3.2 spec created
Topics: config-revamp, config-precedence, bootstrap-on-init, bootstrap-on-run, non-overwrite-config
Affects-phases: phase-3.2-config-strategy-revamp
Affects-docs: specs/phases/phase-3.2-config-strategy-revamp/overview.md, specs/phases/phase-3.2-config-strategy-revamp/plan.md, specs/phases/phase-3.2-config-strategy-revamp/tasks.md
Detail: Defined a dedicated phase for revamping config and generated-data handling so missing config files can be created safely, config always overrides generated resume data, and existing user-edited files are never overwritten.

[NOTE] 2026-04-23 — Expanded final field contract and code impact map
Topics: config-schema, runtime-consumers, csv-export, resume-parser, scoring, apply-flow
Affects-phases: phase-3.2-config-strategy-revamp
Affects-docs: specs/phases/phase-3.2-config-strategy-revamp/overview.md, specs/phases/phase-3.2-config-strategy-revamp/plan.md, specs/phases/phase-3.2-config-strategy-revamp/tasks.md
Detail: Added the full field tables for app.yaml, user.yaml, platform.yaml, and profile_cache.json plus a code impact map covering config loading, resume parsing, search, scoring, apply, workflow, and CSV export review points.

[NOTE] 2026-04-23 — Restructured phase into 3 subphases
Topics: phase-partitioning, schema-foundation, runtime-migration, validation-cleanup
Affects-phases: phase-3.2-config-strategy-revamp
Affects-docs: specs/phases/phase-3.2-config-strategy-revamp/overview.md, specs/phases/phase-3.2-config-strategy-revamp/plan.md, specs/phases/phase-3.2-config-strategy-revamp/tasks.md
Detail: Split the parent config strategy phase into three execution subphases: schema/bootstrap foundation, runtime migration, and validation/cleanup. This keeps the overall work cohesive while still making implementation and review incremental.

[NOTE] 2026-04-23 — Added execution order and exit criteria
Topics: implementation-order, exit-criteria, schema-bootstrap, runtime-migration
Affects-phases: phase-3.2-config-strategy-revamp
Affects-docs: specs/phases/phase-3.2-config-strategy-revamp/plan.md, specs/phases/phase-3.2-config-strategy-revamp/tasks.md
Detail: Expanded the phase plan with file-by-file execution order, concrete deliverables, and exit criteria so implementation can begin without further ambiguity.

---

[NOTE] 2026-04-23 — Phase 3.2 implemented and e2e test passed
Topics: config-revamp, bootstrap-on-init, bootstrap-on-run, backward-compat, config-precedence
Affects-phases: none
Affects-docs: specs/status.md, specs/phases/phase-3.2-config-strategy-revamp/tasks.md
Detail: 3-file config model (app.yaml, user.yaml, platform.yaml) fully implemented with bootstrap helpers, backward compat layer for old field names, non-overwrite policy, and config precedence (platform > app > user > cache > defaults). End-to-end pipeline test passed with auto-apply. 3.2c unit tests deferred by user decision.

[NOTE] 2026-05-19 — Tracking files updated to reflect completion
Topics: phase-completion, tracking-sync
Affects-phases: none
Affects-docs: specs/status.md, specs/phases/phase-3.2-config-strategy-revamp/tasks.md
Detail: tasks.md and status.md were out of sync with actual implementation state. Updated tasks.md to mark 3.2a and 3.2b complete, 3.2c tests as deferred. Status.md updated to list Phase 3.2 as complete.

[NOTE] 2026-05-19 — Deduplicate app.yaml search/profile overlap; migrate code callsites
Topics: config-schema, deduplication, search-config, work-mode
Affects-phases: none
Affects-docs: specs/changelog/2026-05.md
Detail: Removed preferred_roles, preferred_locations, company_size_preference, industry_preference, title_exclude_keywords, remote_preference from AppProfile — all now live exclusively in SearchConfig. Added work_mode_preference scalar to SearchConfig replacing remote_preference. Updated 6 code callsites across naukri.py, engine.py, llm_scorer.py, nodes.py. Fixed bug where primary_stack (tech skills) was incorrectly overriding search.platforms. Widened notice_period to accept int or str.

[NOTE] 2026-05-19 — Config schema extended with 5 new fields for better search + apply
Topics: config-schema, education, certifications, profile-urls, seniority, company-rating
Affects-phases: none
Affects-docs: specs/changelog/2026-05.md
Detail: Added UserEducation model (degree/specialization/institution/year/grade) and UserProfileUrls (github/linkedin/portfolio) to user.yaml; added certifications list to UserExperience; added seniority_level list and min_company_rating float to SearchConfig in app.yaml. All templates and live configs updated. 33 tests still passing.

[NOTE] 2026-05-19 — 3.2c tests implemented — 33 passing
Topics: config-tests, csv-export-stability, backward-compat, bootstrap, non-overwrite, resume-seeding
Affects-phases: none
Affects-docs: specs/phases/phase-3.2-config-strategy-revamp/tasks.md
Detail: Created tests/test_config.py with 33 unit tests covering all 3.2c categories: missing-file bootstrap, non-overwrite behavior, backward compat old field migration, config precedence and defaults, resume seeding, platform/role-family overrides, and CSV export column schema stability. All 33 tests pass.
