---
description: Sync all relevant documents based on the active phase's history log
---
Sync all relevant documents based on the active phase's history log.
Token-efficient: reads history + 2 tiny indexes first, then only targeted files.

## Steps
### Step 1: Load history and indexes (cheap reads)
- Read `specs/status.md` → identify active phase
- Read `specs/phases/phase-N-*/history.md` → extract all entries
- Read `specs/phases/index.json` (~2KB)
- Read `specs/decisions/impact-map.json` (~3KB)

### Step 2: Build targeted file list
For each history entry:
- Extract Topics list
- Look up each topic in `index.json` → collect affected phase `tasks.md` files
- Look up each topic in `impact-map.json` → collect affected doc files/sections

### Step 3: Show sync plan (ALWAYS show before touching anything)
Present to user:
"Based on phase history, I will check and potentially update:
- [list of files]
Proceed? (yes/no)"
If user says no → stop.

### Step 4: Read and assess (targeted reads only)
For each file in the list:
- Read only the relevant section (not the whole file if section is specified)
- Assess: does it need updating based on history entries?
- If yes: note what change is needed

### Step 5: Make updates (one at a time, fully visible)
For each file that needs updating:
- Show the user what will change: "Updating [file]: [description of change]"
- Use the Edit tool to make the change
- The user sees every Edit call

### Step 6: Update phase index if scope changed
If any `[SCOPE_CHANGE]` entries exist:
- Update `specs/phases/index.json` for the active phase's topic list

### Step 7: Commit all changes
```bash
git add specs/ docs/
git commit -m "docs(phase-N): sync docs from phase history"
```

### Step 8: Confirm completion
"Doc sync complete. Updated N files:
- [list of updated files]"

### Safeguards
- NEVER update files not in the targeted list
- ALWAYS show the plan (Step 3) before making any edits
- History entries are NEVER modified — only read
- If unsure whether a doc needs updating, skip it and mention it to the user
