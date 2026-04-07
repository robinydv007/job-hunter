# Phase 2a — History Log

> Append-only log. Never edit existing entries. Format: [TYPE] YYYY-MM-DD — Short title

---

[NOTE] 2026-04-07 — Phase 2a Detailed Profile initiated
Topics: phase-start, detailed-profile, config-split
Affects-phases: phase-2b-auto-apply
Affects-docs: specs/status.md, specs/phases/index.json
Detail: Phase 2a (Detailed Profile) started. This phase implements: screening.yaml split from user.yaml, single LLM call for both basic + detailed profile, profile_detailed.yaml auto-generation, resume_path with default resume.pdf, detailed profile available for all LLM operations.