# Phase 3.2 — History: Config Strategy Revamp

> Phase started: TBD

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
