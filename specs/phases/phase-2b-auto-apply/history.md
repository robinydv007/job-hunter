# Phase 2b — History: Auto-Apply

> Phase started: 2026-04-07

---

[EXPLORATION] 2026-04-07 — Naukri Apply Flow Exploration
Topics: naukri, exploration, selectors, sidebar-form
Affects-phases: phase-2b-auto-apply
Affects-docs: specs/phases/phase-2b-auto-apply/overview.md, specs/phases/phase-2b-auto-apply/plan.md
Detail: Created Playwright exploration script to understand actual Naukri apply flow. Discovered `.apply-button` selector triggers a sidebar form (not modal/page). Logged-in users see pre-filled fields including resume upload (input[type="file"]), experience dropdown (#experienceDD), and location input. Updated overview.md with actual selectors and implementation notes.