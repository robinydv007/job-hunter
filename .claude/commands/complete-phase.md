Verify, finalize, and release a completed phase.

## Steps
### Verify
1. Read the phase's acceptance criteria:
   - Read `specs/phases/phase-N-*/overview.md`
2. Verify all tasks are done:
   - Read `specs/phases/phase-N-*/tasks.md`
   - If any `[ ]` unchecked items remain → report to user, do NOT proceed
3. Run project-specific validation (tests, linting, infra checks).
4. Check for new bugs discovered during the phase:
   - Grep `specs/backlog/backlog.md` for items tagged to this phase

### Finalize
**Step F0: Sync docs from phase history (run BEFORE other finalize steps)**
- Run `/sync-docs` to propagate all history-recorded changes to relevant documents
- This must complete before creating the retrospective, as the retrospective references updated docs
- If /sync-docs finds nothing to update, proceed directly

1. Create retrospective in the phase directory:
   - `specs/phases/phase-N-*/retrospective.md`
   - What went well, what didn't, lessons learned
2. Update all tracking:
   - `specs/phases/README.md` → mark `Complete`
   - `specs/status.md` → update current phase to next, add release version
   - `specs/roadmap/roadmap.md` → update phase status
   - `specs/changelog/YYYY-MM.md` → add release entry

### Release
**Git flow: `phase-N-shortname → staging → main → tag + GitHub Release`**
Never tag or release directly from a phase branch.
1. Commit all remaining changes on phase branch and push:
   ```bash
   git add -A
   git commit -m "docs: complete Phase N - {phase name}"
   git push origin phase-N-shortname
   ```
2. Merge phase branch → staging (ask user for approval first):
   ```bash
   git checkout staging
   git merge --no-ff phase-N-shortname -m "merge: phase-N-shortname → staging (vX.Y.Z)"
   git push origin staging
   ```
3. Merge staging → main (ask user for approval first):
   ```bash
   git checkout main
   git merge --no-ff staging -m "merge: staging → main (vX.Y.Z — Phase N: {phase name})"
   git push origin main
   ```
4. Tag on main + create GitHub Release (ask user for approval first):
   ```bash
   git checkout main
   git tag -a vX.Y.Z -m "Phase N: {phase name}"
   git push origin vX.Y.Z
   gh release create vX.Y.Z \
     --title "vX.Y.Z — Phase N: {phase name}" \
     --notes "## Phase N: {phase name}\n\nNext: Phase N+1 — {next phase name}" \
     --target main
   ```
5. Report summary to user:
   - What was delivered this phase
   - GitHub Release URL (returned by `gh release create`)
   - What's next (phase name + key deliverables)
   - Remind to delete phase branch after merge: `git push origin --delete phase-N-shortname`
