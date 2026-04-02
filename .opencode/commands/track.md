---
description: Track a backlog item — bug, feature, tech debt, or enhancement
---
Track a backlog item — bug, feature, tech debt, or enhancement. Use $ARGUMENTS for the item description.

## Steps
1. Read the backlog to find the next available ID:
   - Read `specs/backlog/backlog.md`
2. Determine the item type from $ARGUMENTS:
   - Bug → `BUG-NNN` — add to Bugs table
   - Feature → `FEAT-NNN` — add to Features table
   - Tech Debt → `TD-NNN` — add to Tech Debt table
   - Enhancement → `ENH-NNN` — add to Enhancements table
3. Add a row to the appropriate table in `specs/backlog/backlog.md`:
   - `Priority`: Infer from urgency (default `P2`)
   - `Status`: `open`
   - `Phase`: Target phase or `unscheduled`
   - `Detail`: `—` unless complex
4. If the item is complex (needs acceptance criteria, investigation notes):
   - Create `specs/backlog/details/{ID}.md` with YAML frontmatter:
   ```yaml
   id: {ID}
   title: "{title}"
   priority: {P0-P3}
   status: open
   phase: {phase or unscheduled}
   created: {YYYY-MM-DD}
   ```
   - Update the `Detail` column to `[→](details/{ID}.md)`
5. If this is P0, also update the Critical Items table in `specs/status.md`.
6. Commit:
   ```bash
   git add specs/backlog/
   git commit -m "docs(backlog): add {ID} - {short title}"
   ```
