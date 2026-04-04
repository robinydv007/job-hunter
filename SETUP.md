# Setup — What to Do After Cloning

You've cloned the SDD template. Here's how to start your project.

## 1. Rename the Repo

```bash
# If you cloned, change the remote
git remote set-url origin https://github.com/<your-org>/<your-project>.git
```

## 2. Write Your Vision Document

Create `docs/<your-project>.md` — this is the master plan the agent reads to understand what you're building. Include:
- What problem you're solving
- Who it's for
- Key features
- Technical constraints (language, framework, hosting)
- Success criteria

## 3. Update Placeholders

Find and replace these in the spec files:
- `YYYY-MM-DD` → today's date
- `YYYY-MM` → current month
- `<project-name>` → your project name
- `<Phase 0 Name>` → what you're calling Phase 0 (usually "Bootstrap" or "Foundation")

Files that need updating:
- `specs/status.md`
- `specs/roadmap/roadmap.md`
- `specs/changelog/YYYY-MM.md` (rename file to match current month)
- `specs/phases/index.json`

## 4. Run the Compliance Check

```bash
bash scripts/check-sdd-compliance.sh
```

Should pass with no errors.

## 5. Start Phase 0

Run `/start-phase` in your agent session. The agent will:
- Create `specs/phases/phase-0-<name>/` with overview, plan, tasks, history
- Update `specs/status.md` to Phase 0 in-progress
- Create a git branch
- Build the topic index

## 6. Write Your First Feature

Once Phase 0 is planned, start implementing. The agent will:
- Auto-update tracking after each change
- Auto-record decisions to history
- Block commits if tracking is out of sync

## The Workflow

```
1. DISCOVER  → Agent reads status.md + backlog.md
2. PLAN      → Agent creates phase plan (you approve)
3. IMPLEMENT → Agent writes code, auto-updates tracking
4. VERIFY    → Tests, validation, checks
5. SYNC      → /sync-docs propagates history to docs
6. RELEASE   → /complete-phase tags, merges, retrospective
```

## Quick Reference

| Need | File to Read | Command |
|------|-------------|---------|
| What's the current state? | `specs/status.md` | — |
| What's in the backlog? | `specs/backlog/backlog.md` | `/review` |
| Start a new phase | — | `/start-phase` |
| Add a bug/feature | — | `/track` |
| Record a decision | — | `/log` |
| Complete a phase | — | `/sync-docs` then `/complete-phase` |
| Full guide | `docs/developer-guideline.md` | — |
