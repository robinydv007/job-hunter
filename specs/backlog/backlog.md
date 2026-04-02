# Backlog
**Last Updated**: 2026-04-02
**Convention**: Simple items stay in this table. Complex items get a detail file: `[→](details/ID.md)`

## Priority Levels
| Level | Meaning |
|-------|---------|
| **P0** | Critical — blocks current phase |
| **P1** | High — address in current/next phase |
| **P2** | Medium — address within 2 phases |
| **P3** | Low — nice to have |

**Status**: `open` | `in-progress` | `resolved` | `deferred` | `deprecated`

## Bugs
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| BUG-001 | Roadmap shows Phase 0 as Not Started | P2 | open | phase-0-bootstrap | `specs/roadmap/roadmap.md:8` shows `Not Started` but phase is Complete |
| BUG-002 | Retrospective metrics show 14 tasks instead of 15 | P3 | open | phase-0-bootstrap | `specs/phases/phase-0-bootstrap/retrospective.md:36-37` says planned/completed: 14, actual is 15 |
| BUG-003 | Success criteria checkboxes unchecked for Phase 0 | P2 | open | phase-0-bootstrap | `specs/vision/success-criteria.md:6-8` all unchecked despite Phase 0 completion |
| BUG-004 | Plan risk table references old Claude Code approach | P3 | open | phase-0-bootstrap | `specs/phases/phase-0-bootstrap/plan.md:24` risk mentions PostToolUse hook that was replaced |
| BUG-005 | `[NOTE]` entry type inconsistency between CLAUDE.md and .agent/rules | P3 | open | phase-0-bootstrap | `.agent/rules/project.md` includes `[NOTE]` entry type, `CLAUDE.md` does not |
| BUG-006 | Developer guideline references wrong vision doc path | P2 | open | phase-0-bootstrap | `docs/developer-guideline.md:88` says vision goes in `docs/` but it's in `specs/vision/` |
| BUG-007 | Duplicate command definitions in opencode.json and .opencode/commands/ | P1 | open | phase-0-bootstrap | `opencode.json` has full `command` block AND `.opencode/commands/*.md` files exist — could cause conflicts |

## Features
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| _(none yet)_ | | | | | |

## Tech Debt
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| _(none yet)_ | | | | | |

## Enhancements
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| _(none yet)_ | | | | | |
