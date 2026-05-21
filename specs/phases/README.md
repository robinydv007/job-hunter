# Phases Index
Quick reference for all phases. See [roadmap](../planning/roadmap.md) for timeline.

| Phase | Name | Status | Directory |
|-------|------|--------|-----------|
| 0 | Foundation & Infrastructure | ✅ Complete | `phase-0-foundation/` |
| 1 | MVP Core Pipeline | ✅ Complete | `phase-1-mvp-pipeline/` |
| 2a | Detailed Profile & Config Restructure | ✅ Complete | `phase-2a-detailed-profile/` |
| 2b | Auto-Apply & Batch Screening | ✅ Complete | `phase-2b-auto-apply/` |
| 3.2 | Config Strategy Revamp | ✅ Complete | `phase-3.2-config-strategy-revamp/` |
| 3.0 | Async Architecture Foundation | 🔄 In Progress | `phase-3.0-async-foundation/` |
| 3.1 | Multi-Platform & Intelligence | 🔲 Planned | _(not started)_ |

Each phase directory contains:
| File | Purpose |
|------|---------|
| `overview.md` | Goal, scope, deliverables, acceptance criteria, exit criteria |
| `plan.md` | Implementation approach, module structure, risks |
| `tasks.md` | Detailed checklist with verification steps |
| `history.md` | Append-only log of decisions, scope changes, discoveries (drives /sync-docs) |
| `retrospective.md` | Post-completion review (created by /complete-phase) |

## Dependencies
```
Phase 0 (Foundation & Infrastructure)     ← COMPLETE
└── Phase 1 (MVP Core Pipeline)             ← COMPLETE
    └── Phase 2a (Detailed Profile)         ← COMPLETE
        ├── Phase 2b (Auto-Apply)           ← COMPLETE
        └── Phase 3.2 (Config Revamp)       ← COMPLETE
            └── Phase 3.0 (Async Arch)      ← IN PROGRESS
                └── Phase 3.1 (Multi-Platform) ← PLANNED
```
