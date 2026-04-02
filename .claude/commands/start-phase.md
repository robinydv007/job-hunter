Begin a new implementation phase.

## Steps
1. Read current state:
   - Read `specs/status.md`
2. Check for blocking bugs (Rule 4 — pre-phase bug check):
   - Scan `specs/backlog/backlog.md` for P0/P1 items
   - If P0 bugs exist → report to user, recommend fixing first
   - If only P1 → continue but note them
3. Create the phase directory if it doesn't exist:
   `specs/phases/phase-N-shortname/`
   - overview.md ← Scope, goals, deliverables, acceptance criteria
   - plan.md ← Implementation approach, steps, risks
   - tasks.md ← Detailed checklist

Use existing phase directories as reference (e.g., `phase-0-bootstrap/`).

4. Build phase topic index:
   - Read the phase's `overview.md` and `tasks.md`
   - Extract key topics: technology names, services, architectural concepts
   - Add/update the phase entry in `specs/phases/index.json`:
   ```json
   "phase-N-name": {
     "status": "in-progress",
     "topics": ["topic-1", "topic-2", ...]
   }
   ```
5. Create the phase history file: `specs/phases/phase-N-name/history.md` from the template
6. Update `specs/phases/README.md`:
   - Change phase status: `Not Started` → `In Progress`
   - Add link to the phase directory
7. Update `specs/status.md`:
   - Set "Current Phase" to the new phase
   - Update "Active Phase" table
   - Clear/update blockers
8. Create git branch and initial commit:
   ```bash
   git checkout main && git pull origin main
   git checkout -b phase-N-shortname
   git add specs/
   git commit -m "docs: start Phase N - {phase name}"
   git push -u origin phase-N-shortname
   ```
9. Update `specs/changelog/YYYY-MM.md` with phase start entry.
