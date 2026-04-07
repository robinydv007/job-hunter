# Phase 2a — Plan: Detailed Profile

## Implementation Approach

Modify the existing resume parser to extract both basic and detailed profiles in a single LLM call. Add config loading for the new screening.yaml file.

---

### Module Design

#### 1. Config Loading (`config/__init__.py`)

**Strategy:** Load both user.yaml and screening.yaml, merge into single config object.

```
user.yaml → Profile, Search, Naukri, Scoring, AutoApply
screening.yaml → ScreeningConfig (screening_answers + screening_answers_extended)
```

- Create `ScreeningConfig` Pydantic model
- Add `screening` field to `AppConfig`
- Add `resume_path` to `Profile` model
- Load both YAML files in `load_config()`

#### 2. Resume Parser (`resume/parser.py`)

**Strategy:** Single LLM call returns both basic and detailed profile data.

```
resume file → extract text → LLM (single prompt with two sections) 
→ parse JSON → (ResumeProfile, detailed_dict) → save both files
```

**Key functions to modify/add:**
- `parse_resume_full(resume_path)` - new function returning tuple
- Modify `parse_resume()` to use the new function
- `save_detailed_profile(detailed_data)` - save to YAML
- `load_detailed_profile()` - load from YAML
- `should_regenerate_profile()` - compare file hash/mtime

**Cache logic:**
1. Check if resume file changed (hash or mtime)
2. If changed → regenerate both profiles
3. If not changed → load both from cache files
4. If cache files don't exist → generate and save

#### 3. File Structure

- **screening.yaml**: New config file (moved from user.yaml)
- **profile_detailed.yaml**: New data file (auto-generated)
- **user.yaml**: Remove screening_answers section

---

### Data Flow

```
User runs: job-hunter run --resume resume.pdf

         ┌──────────────────────────────┐
         │ load_config()               │
         │ - Load user.yaml             │
         │ - Load screening.yaml        │
         │ - Merge into AppConfig       │
         └──────────────────────────────┘
                      │
                      ▼
         ┌──────────────────────────────┐
         │ parse_resume_node()          │
         │ - Check resume file changed? │
         │ - If yes: single LLM call    │
         │   → basic + detailed         │
         │ - If no: load from cache     │
         │ - Save profile.json          │
         │ - Save profile_detailed.yaml │
         └──────────────────────────────┘
```

---

### Dependencies

- Phase 1 complete (resume parser, config loading, LangGraph nodes)

---

### Risks Identified

| Risk | Mitigation |
|------|------------|
| LLM JSON structure changes | Pydantic validation; fallback to error with clear message |
| YAML load/save errors | Try/except with user-friendly error |
| Resume file not found | Check existence before parsing; clear error message |
| Cache corruption | Validate loaded data; regenerate if invalid |

---

## Effort

~1-2 days for Phase 2a - primarily config restructuring and parser modification.