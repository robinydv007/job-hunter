# Spec-Driven Development Template

A ready-to-use project management system for spec-driven development with AI agents.

## What This Is

This repository provides a complete **spec-driven development (SDD)** workflow:
- Every phase of work is planned before coding starts
- AI agents and developers share the same source of truth (`specs/`)
- Tracking is automatic — agents update status, changelog, and tasks as they work
- Phase history captures decisions and discoveries as they happen
- Git discipline is built in — automatic branching, atomic commits, safe merges
- Enforcement prevents drift — commits blocked if tracking is out of sync

## Quick Start

1. **Clone this repo** as your new project
2. **Write your vision document** in `docs/<project-name>.md`
3. **Run `/start-phase`** to begin Phase 0
4. **Follow the cycle**: Plan → Implement → Verify → Sync → Release

## Structure

| Path | Purpose |
|------|---------|
| `specs/` | Single source of truth — status, backlog, phases, decisions, roadmap |
| `docs/` | Developer documentation and vision |
| `.opencode/commands/` | Slash commands for phase workflows |
| `.opencode/plugins/` | Event hooks (history reminder, enforcement) |
| `opencode.json` | Project config (commands, instructions) |
| `.agent/rules/` | Agent operational rules |
| `scripts/` | Automation hooks (compliance checker, pre-commit) |

## Key Commands

| Command | Purpose |
|---------|---------|
| `/start-phase` | Begin a new implementation phase |
| `/complete-phase` | Verify and release a completed phase |
| `/sync-docs` | Propagate phase history to docs |
| `/log` | Record a manual history entry |
| `/track` | Add a backlog item |
| `/review` | Groom the backlog between phases |

## Development Cycle

```
DISCOVER → PLAN → IMPLEMENT → VERIFY → SYNC → RELEASE
```

See `docs/developer-guideline.md` for the complete guide.
