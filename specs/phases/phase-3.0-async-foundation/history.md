# Phase 3.0 — History: Async Architecture Foundation

> Phase started: TBD

---

[NOTE] 2026-04-08 — Phase 3.0 spec created
Topics: async-architecture, nest_asyncio-removal, login-node, pipeline-reorder
Affects-phases: phase-3.0-async-foundation, phase-3.1-multi-platform
Affects-docs: specs/phases/phase-3.0-async-foundation/overview.md, specs/phases/phase-3.0-async-foundation/plan.md, specs/phases/phase-3.0-async-foundation/tasks.md
Detail: Created comprehensive spec for Phase 3.0 — converting the entire pipeline from sync+nest_asyncio to native async, adding login_platforms node, and reordering the pipeline so resume parsing happens before login. This resolves ENH-017 which failed twice due to async/sync conflicts.

[FEATURE] 2026-04-22 — ENH-021 implemented: merge resume cache to single profile_cache.json
Topics: profile-cache-consolidation
Affects-phases: phase-3.0-async-foundation
Affects-docs: specs/phases/phase-3.0-async-foundation/tasks.md
Detail: Consolidated profile.json + profile_detailed.yaml into single profile_cache.json. Simplified loader functions, updated CLI clean command, and added detailed field to ResumeProfile schema. Enables ENH-022 user overrides.

[FEATURE] 2026-04-22 — ENH-022 implemented: user-owned config/profile.yaml
Topics: user-owned-profile-config
Affects-phases: phase-3.0-async-foundation
Affects-docs: specs/phases/phase-3.0-async-foundation/tasks.md, specs/backlog/backlog.md
Detail: Added ProfileOverrides and ProfileEnrichment Pydantic models, load_profile_yaml() in load_config(), merge_profile_with_overrides() helper in parser.py, and init command creates profile.yaml template. User overrides survive re-parse.

---

[NOTE] 2026-05-21 — Pre-start spec refresh after Phase 3.2 completion
Topics: async-architecture, nest_asyncio-removal, spec-refresh, phase-3.2-impact
Affects-phases: none
Affects-docs: specs/phases/phase-3.0-async-foundation/tasks.md, specs/phases/phase-3.0-async-foundation/plan.md
Detail: Audited current code against Phase 3.0 spec before starting implementation. Found that Tasks 1 and 2 (search_naukri and parse_resume_node async conversion) were completed during Phase 3.2, and workflow.ainvoke is already in use. Updated tasks.md to mark these done. Also resolved the nest_asyncio handling question for llm_scorer.py: replace with asyncio.run() rather than deleting the sync wrapper. Updated plan.md to reflect Phase 3.2's 3-file config model in the CLI initial_state example.