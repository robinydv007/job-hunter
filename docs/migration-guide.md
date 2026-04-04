# Migrating an Existing Project to SDD

You have an existing codebase. Here's how to adopt the spec-driven development system without starting over.

## The Core Idea

You don't start from Phase 0. You **backfill what matters** and start from wherever your project actually is. The system self-improves — within 1-2 phases of using it, the tracking becomes comprehensive.

## Step 1: Copy SDD Files Into Your Repo

```bash
# From your existing project root
cp /path/to/sdd-template/CLAUDE.md .
cp /path/to/sdd-template/opencode.json .
cp -r /path/to/sdd-template/.agent/ .
cp -r /path/to/sdd-template/.opencode/ .
cp -r /path/to/sdd-template/scripts/ .
cp -r /path/to/sdd-template/specs/ .
cp /path/to/sdd-template/docs/developer-guideline.md docs/

# Install plugin dependencies
cd .opencode && npm install && cd ..

# Install git hook
git config core.hooksPath scripts/
```

## Step 2: Determine Your Current Phase

Ask yourself: **How much have we shipped?**

| Your Project State | Your Phase | What to Do |
|---|---|---|
| Just starting, nothing shipped | Phase 0 | Start fresh with `/start-phase` |
| MVP shipped, iterating | Phase 1 | Backfill Phase 0 as "complete", start Phase 1 |
| Multiple features shipped | Phase 2+ | Backfill Phase 0 as "complete", start at current phase |
| Production, mature project | Phase N | Backfill Phase 0, start at current phase |

## Step 3: Minimal Backfill

### Must Do (5 minutes)

**1. Set `specs/status.md` to your current state:**
```markdown
**Current Phase**: Phase 1 — <your current work> (`not-started`)
**Latest Release**: vX.Y.Z (or "None" if not released)
```

**2. Rename the changelog file:**
```bash
mv specs/changelog/2026-04.md specs/changelog/$(date +%Y-%m).md
```

**3. Add known bugs to backlog:**
Open `specs/backlog/backlog.md` and add any known issues:
```markdown
| BUG-001 | Login fails with special chars | P1 | open | unscheduled | — |
```

### Should Do (15 minutes)

**4. Write a quick vision doc:**
Create `docs/<project-name>.md` with:
- What your project does (1 paragraph)
- Who it's for
- Key features (bullet list)
- Tech stack

**5. Create your current phase directory:**
```bash
mkdir -p specs/phases/phase-N-<name>/
```
Create `overview.md` with what you're working on right now.

**6. Update the roadmap:**
Edit `specs/roadmap/roadmap.md` with your actual timeline.

### Nice to Have (30 minutes)

**7. Backfill ADRs for major decisions:**
For each significant technical choice already made:
```bash
cp specs/decisions/0000-template.md specs/decisions/NNNN-<decision>.md
```
Fill in Context, Decision, Alternatives, Consequences. Doesn't need to be perfect — just capture the rationale.

**8. Populate the impact map:**
As you write ADRs, add topics to `specs/decisions/impact-map.json`.

**9. Create minimal "completed" phase directories:**
For phases you've already shipped, create the directory with just a `retrospective.md`:
```markdown
# Phase 0 — Bootstrap: Retrospective
Shipped before SDD was adopted. Minimal backfill.
```

## Step 4: Start Your Next Phase

Run `/start-phase` in your agent session. The agent will:
- Create the phase directory with overview, plan, tasks, history
- Update `specs/status.md` to in-progress
- Create a git branch
- Build the topic index

From this point forward, the full SDD system is active.

## What to Skip

| Skip This | Why |
|-----------|-----|
| Perfect backfill of old ADRs | It grows organically as you work |
| Creating directories for every past phase | Just create the current one |
| Filling the impact-map.json completely | It builds up over 1-2 phases |
| Rewriting git history | Don't touch existing commits |

## Common Pitfalls

| Pitfall | How to Avoid |
|---------|-------------|
| Trying to backfill everything perfectly | The system self-improves — start with minimal backfill |
| Setting Phase 0 when you're actually at Phase 3 | Be honest about where you are |
| Not adding known bugs to backlog | Do this first — Rule 4 checks for P0 bugs before each phase |
| Forgetting to run `git config core.hooksPath scripts/` | The enforcement hook won't work without this |
| Keeping old `.claude/` directory if migrating from Claude Code | Delete it — use `.opencode/` instead |

## After Migration

Your first SDD-managed phase will feel different from your old workflow:
- **Before**: Code first, document later (if ever)
- **After**: Plan first, code with auto-tracking, sync docs at completion

The enforcement system will block commits if tracking is out of sync. This feels restrictive at first, but it prevents the drift that makes project docs useless over time.

Within 1-2 phases, the system becomes comprehensive and you'll have:
- Accurate status tracking
- Decision history with ADRs
- Clean changelog
- Populated impact map
- Phase retrospectives
