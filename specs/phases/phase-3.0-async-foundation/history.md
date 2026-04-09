# Phase 3.0 — History: Async Architecture Foundation

> Phase started: TBD

---

[NOTE] 2026-04-08 — Phase 3.0 spec created
Topics: async-architecture, nest_asyncio-removal, login-node, pipeline-reorder
Affects-phases: phase-3.0-async-foundation, phase-3.1-multi-platform
Affects-docs: specs/phases/phase-3.0-async-foundation/overview.md, specs/phases/phase-3.0-async-foundation/plan.md, specs/phases/phase-3.0-async-foundation/tasks.md
Detail: Created comprehensive spec for Phase 3.0 — converting the entire pipeline from sync+nest_asyncio to native async, adding login_platforms node, and reordering the pipeline so resume parsing happens before login. This resolves ENH-017 which failed twice due to async/sync conflicts.