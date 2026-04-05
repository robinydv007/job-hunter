# Developer Guideline

**How to work with this spec-driven development system**

---

## Quick Start

**New project?** Read [`SETUP.md`](../SETUP.md) first — it has the step-by-step onboarding flow.

**Adding to existing project?** Read [`docs/migration-guide.md`](migration-guide.md).

1. **Always start here**: Read `specs/status.md` to understand the current phase and any blockers
2. **Check the backlog**: Look at `specs/backlog/backlog.md` for pending work
3. **Understand your phase**: Read the phase directory in `specs/phases/phase-N-*/`

## System Overview

This project uses **spec-driven development (SDD)** with AI agents. The `specs/` directory is the single source of truth for all work. Before writing any code, the agent plans in specs. After writing code, the agent updates tracking automatically.

### Directory Structure
```
/
├── CLAUDE.md              # Agent configuration (opencode reads as fallback)
├── opencode.json          # OpenCode project config (commands, plugins, instructions)
├── README.md              # Project overview
├── docs/                  # Developer documentation
│   └── developer-guideline.md  # This file
├── specs/                 # THE SOURCE OF TRUTH
│   ├── status.md          # Current phase, blockers, P0 items
│   ├── architecture/      # System architecture docs (overview, diagrams)
│   │   └── overview.md    # High-level system design and component map
│   ├── product/           # All product features across all phases (phase-agnostic)
│   │   └── requirements.md # Feature registry — WHAT the product does
│   ├── backlog/           # All work items (bugs, features, tech debt)
│   ├── changelog/         # Monthly changelogs
│   ├── decisions/         # Architecture Decision Records (ADRs)
│   ├── phases/            # Per-phase plans, tasks, history
│   ├── roadmap/           # Timeline and milestones
│   └── vision/            # Project charter, principles, success criteria
├── scripts/               # Automation scripts
├── .opencode/             # OpenCode configuration
│   ├── commands/          # Slash command definitions (markdown with frontmatter)
│   └── plugins/           # JavaScript/TS plugins (hooks, automation)
└── .agent/
    └── rules/
        └── project.md     # Detailed agent rules
```

## Core Concepts

### Spec Layer Separation

Each `specs/` folder answers a distinct question. Don't mix concerns across layers:

| Layer | Answers | Changes When |
|---|---|---|
| `specs/vision/` | *Why does this exist? What are we trying to achieve?* | Vision shifts (rare) |
| `specs/product/` | *What does the product do? All features across all phases?* | Features added or changed |
| `specs/architecture/` | *How is the system built technically?* | Tech decisions change |
| `specs/roadmap/` | *When are things happening? Phase timeline?* | Timeline shifts |
| `specs/phases/` | *What exactly did we do in this iteration?* | Per-phase work |
| `specs/decisions/` | *Why did we choose this over alternatives?* | A significant decision is made |
| `specs/backlog/` | *What work is pending, blocked, or planned?* | Work items added/resolved |

### Phases
Work is broken into phases. Each phase has:
- `overview.md` — What we're building and why
- `plan.md` — How we'll build it
- `tasks.md` — Detailed checklist
- `history.md` — Append-only log of decisions and discoveries
- `retrospective.md` — Post-completion review (created when phase completes)

### Tracking System
| File | Purpose |
|------|---------|
| `specs/status.md` | Current state — **read this first** |
| `specs/product/requirements.md` | All product features — **read to understand what we're building** |
| `specs/architecture/overview.md` | System design — read before architectural changes |
| `specs/backlog/backlog.md` | All work items with priorities |
| `specs/changelog/YYYY-MM.md` | What changed each month |
| `specs/decisions/` | Why technical choices were made |
| Phase `tasks.md` | Detailed progress tracking |

### Priorities
| Level | Meaning | Action |
|-------|---------|--------|
| P0 | Critical — blocks current phase | Fix immediately |
| P1 | High | Address in current/next phase |
| P2 | Medium | Address within 2 phases |
| P3 | Low | Nice to have |

### Backlog Item IDs
| Type | Prefix | Example |
|------|--------|---------|
| Bug | `BUG-` | `BUG-001` |
| Feature | `FEAT-` | `FEAT-001` |
| Tech Debt | `TD-` | `TD-001` |
| Enhancement | `ENH-` | `ENH-001` |

## Working with the Agent

### What the Agent Does Automatically
1. **Reads status first** — Always starts with `specs/status.md`
2. **Updates tracking** — After any meaningful work, updates tasks.md, status.md, and changelog
3. **Tracks discoveries** — Bugs and tech debt found during work go to backlog immediately
4. **Records history** — Decisions and discoveries logged to phase history.md
5. **Manages git** — Creates branches, makes atomic commits, pushes to remote
6. **Plans before coding** — Uses plan mode for non-trivial work

### What You Should Do
1. **Write the vision** — See [`SETUP.md`](../SETUP.md) for the onboarding flow
2. **Review plans** — Agent presents plans before implementing; approve or request changes
3. **Use slash commands** — Trigger phase workflows (see below)
4. **Review between phases** — Use `/review` to groom the backlog

## Slash Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/start-phase` | Begin a new phase | Starting new work |
| `/complete-phase` | Verify and release a phase | All phase tasks done |
| `/sync-docs` | Propagate history to docs | Before completing a phase |
| `/log` | Record a manual history entry | Agent missed something |
| `/track` | Add a backlog item | Found a bug or have an idea |
| `/review` | Groom the backlog | Between phases |

## Development Cycle

```
1. DISCOVER → Agent reads status.md + backlog.md
2. PLAN → Agent reads/creates phase plan.md (requires your approval)
3. IMPLEMENT → Agent writes code, auto-updates tracking
4. VERIFY → Tests, validation, checks
5. SYNC → /sync-docs propagates history to docs
6. RELEASE → /complete-phase tags, merges, writes retrospective
```

## Git Workflow

### Branch Naming
| Type | Pattern | Example |
|------|---------|---------|
| Phase | `phase-N-shortname` | `phase-0-bootstrap` |
| Feature | `feat/description` | `feat/user-auth` |
| Bug fix | `fix/description` | `fix/state-lock-timeout` |
| Refactor | `refactor/description` | `refactor/module-cleanup` |

### Commit Convention
```
feat(scope): description     # New functionality
fix(scope): description      # Bug fix
infra(scope): description    # Infrastructure changes
docs: description            # Documentation only
refactor(scope): description # Code restructuring
chore: description           # Build/tooling
```

### Merge Flow
```
feature branch → staging → main → tag + release
```
- Agent auto-commits and pushes to feature branches
- **Agent asks before merging** to staging or main
- Never auto-merge to protected branches

## Phase History System

### Why History?
During implementation, decisions change, scope shifts, and new things are discovered. Without tracking, docs drift stale. The solution: **append-only phase history**.

### How It Works
1. Agent logs entries to `specs/phases/phase-N-*/history.md` as it works
2. Entry types: `[DECISION]`, `[SCOPE_CHANGE]`, `[DISCOVERY]`, `[FEATURE]`, `[ARCH_CHANGE]`, `[NOTE]`
3. At phase completion, `/sync-docs` reads history and updates all affected docs
4. History entries are **never modified** — only appended

### Entry Format
```
[TYPE] YYYY-MM-DD — Short title
Topics: topic-1, topic-2
Affects-phases: phase-N-name (or "none")
Affects-docs: path/to/doc.md#section (or "none")
Detail: One to three sentences describing what changed and why.
```

## Enforcement

SDD compliance is enforced at two levels. Commits are **blocked** if tracking is out of sync.

### How It Works
1. **Plugin** (`.opencode/plugins/history-reminder.js`) — intercepts `git commit` before it runs
2. **Pre-commit hook** (`scripts/pre-commit`) — final gate via `core.hooksPath`

Both run `scripts/check-sdd-compliance.sh` which checks:
- No secrets (API keys, tokens, private keys)
- Changelog entry exists for today (if code changed)
- History.md updated (if tasks.md changed)
- Status.md synced (if phase marked Complete)
- Overview.md acceptance criteria checked (if phase marked Complete)

### When a Commit Is Blocked
You'll see an error like:
```
SDD COMPLIANCE CHECK FAILED — commit blocked.
  ✗ CHANGELOG MISSING: No entry for 2026-04-04 in specs/changelog/2026-04.md.
```

**Fix:** Update the missing file, `git add` it, then retry `git commit`.

### Stale Date Warning
If `specs/status.md` has an old `Last Updated` date and code is changing, you'll get a warning (not a block):
```
⚠ STALE DATE: specs/status.md Last Updated is 2026-04-02 but today is 2026-04-04.
```
This is a reminder to keep tracking docs current.

## Architecture Decision Records (ADRs)

### When to Create an ADR
- Choosing a technology or framework
- Making an architectural pattern decision
- Changing a previously made decision
- Any decision that future developers need to understand

### Creating an ADR
1. Copy `specs/decisions/0000-template.md` to `NNNN-kebab-title.md`
2. Fill in all sections
3. Add entry to `specs/decisions/README.md` index
4. Commit: `git commit -m "docs(adr): NNNN — title"`

### ADR Lifecycle
`proposed` → `accepted` | `rejected` | `superseded`

## Best Practices

### For Developers
1. **Read before writing** — Always check specs before changing code
2. **Update tracking** — If you do work outside the agent, update tasks.md and changelog
3. **Use ADRs** — Document significant decisions, don't just make them
4. **Small phases** — Keep phases focused and completable
5. **Groom regularly** — Use `/review` between phases to keep backlog healthy

### For Working with AI Agents
1. **Be specific in vision** — The better your vision doc, the better the agent's plans
2. **Review plans carefully** — Agent presents plans before implementing; this is your control point
3. **Use /log for context** — If the agent misses something important, log it to history
4. **Trust but verify** — Agent auto-updates tracking, but spot-check occasionally
5. **Phase boundaries matter** — Don't skip `/sync-docs` before `/complete-phase`

## Troubleshooting

### "The agent doesn't know what to work on"
- Check `specs/status.md` — is a phase marked as active?
- Check `specs/phases/phase-N-*/tasks.md` — are there unchecked tasks?
- Run `/start-phase` if starting a new phase

### "Docs are out of date"
- Run `/sync-docs` to propagate history to docs
- This should happen automatically at phase completion

### "I found a bug during the phase"
- Use `/track BUG-NNN description` to add it to backlog
- The agent also does this automatically when it finds issues

### "The backlog is messy"
- Run `/review` to groom and re-prioritize
- Best done between phases

## Migrating an Existing Project

See [`docs/migration-guide.md`](migration-guide.md) for the complete guide on adopting SDD in an existing codebase.

## File Naming Conventions

| Location | Convention | Examples |
|----------|-----------|---------|
| `specs/` — folders | `kebab-case` | `phase-0-bootstrap/` |
| `specs/` — files | `kebab-case` | `0001-state-backend-postgres.md` |
| `docs/` — files | `kebab-case` | `developer-guideline.md` |
| `.opencode/commands/` | `kebab-case` | `start-phase.md` |
| `.agent/` — files | `snake_case` | `project.md` |
| ADR files | `NNNN-kebab-title.md` | `0001-state-backend-postgres.md` |
| Phase directories | `phase-N-shortname` | `phase-0-bootstrap` |
| Changelog files | `YYYY-MM.md` | `2026-04.md` |
