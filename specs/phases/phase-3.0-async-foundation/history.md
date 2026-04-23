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