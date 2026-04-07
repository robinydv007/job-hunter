# Phase 2a — History Log

> Append-only log. Never edit existing entries. Format: [TYPE] YYYY-MM-DD — Short title

---

[NOTE] 2026-04-07 — Phase 2a Detailed Profile initiated
Topics: phase-start, detailed-profile, config-split
Affects-phases: phase-2b-auto-apply
Affects-docs: specs/status.md, specs/phases/index.json
Detail: Phase 2a (Detailed Profile) started. This phase implements: screening.yaml split from user.yaml, single LLM call for both basic + detailed profile, profile_detailed.yaml auto-generation, resume_path with default resume.pdf, detailed profile available for all LLM operations.

[FEATURE] 2026-04-07 — Phase 2a implementation completed
Topics: screening.yaml, profile_detailed.yaml, single-llm-call, resume-path, resume-change-detection, config-split
Affects-phases: phase-2b-auto-apply
Affects-docs: specs/status.md, src/job_hunter/config/__init__.py, src/job_hunter/resume/parser.py, src/job_hunter/graph/nodes.py, src/job_hunter/graph/state.py
Detail: Implemented all Phase 2a features: (1) config/__init__.py loads screening.yaml, added resume_path to Profile with default resume.pdf, created ScreeningConfig model; (2) resume/parser.py has parse_resume_full() for single LLM call extracting both basic + detailed profiles, save_detailed_profile/load_detailed_profile functions, resume hash-based change detection in data/resume_hash.txt; (3) nodes.py parse_resume_node updated to use parse_resume_full and return detailed_profile; (4) state.py updated to include detailed_profile field.