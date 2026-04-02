Review and groom the backlog between phases.

## Steps
1. Read current state and backlog:
   - Read `specs/status.md`
   - Read `specs/backlog/backlog.md`
2. For each category (Bugs, Features, Tech Debt, Enhancements), assess:
   - Are priorities still accurate given the current phase?
   - Should any items move to the active/next phase?
   - Are any items now `resolved` or `deprecated`?
   - Are there orphaned items (no phase assigned)?
3. Check for dependencies:
   - P0 bugs that should block phase progress
   - Features that depend on unresolved tech debt
4. Update `specs/backlog/backlog.md` with any priority/status/phase changes.
5. Update `specs/status.md` if P0/blocker items changed.
6. Commit:
   ```bash
   git add specs/
   git commit -m "docs(backlog): grooming for Phase N"
   ```
7. Report to user:
   - Total open items by type and priority
   - P0/P1 items requiring immediate attention
   - Recommended actions before next phase
