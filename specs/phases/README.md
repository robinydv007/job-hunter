# Phases Index
Quick reference for all phases. See [roadmap](../roadmap/roadmap.md) for timeline.

| Phase | Name | Status | Directory |
|-------|------|--------|-----------|
| 0 | Foundation & Infrastructure | ✅ Complete | `phase-0-foundation/` |
| 1 | MVP Core Pipeline | ✅ Complete | `phase-1-mvp-pipeline/` |
| 2 | Auto-Apply & Enrichment | 🔲 Not Started | `phase-2-auto-apply/` *(planned)* |

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
Phase 0 (Foundation & Infrastructure)  ← COMPLETE
└── Phase 1 (MVP Core Pipeline)        ← COMPLETE
    └── Phase 2 (Auto-Apply & Enrichment)  ← NEXT
```
