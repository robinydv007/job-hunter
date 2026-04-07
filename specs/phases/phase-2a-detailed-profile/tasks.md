# Phase 2a — Tasks: Detailed Profile

> **Status: PLANNED** — Ready to start

## Task Checklist

### 1. Config File Restructure
- [ ] Create `config/screening.yaml` file with content moved from user.yaml
- [ ] Remove `screening_answers` section from `config/user.yaml`
- [ ] Add `screening_answers_extended` section to `screening.yaml`
- [ ] Update `src/job_hunter/config/__init__.py`:
  - Create `ScreeningAnswers` model (already exists, verify)
  - Create `ScreeningConfig` model with `screening_answers` and `screening_answers_extended`
  - Add `screening: ScreeningConfig` field to `AppConfig`
  - Update `load_config()` to load both user.yaml and screening.yaml
- [ ] Verify: `load_config()` returns combined config with screening

### 2. Resume Path Field
- [ ] Add `resume_path` field to `Profile` model in `src/job_hunter/config/__init__.py`
- [ ] Add `resume_path` to `config/user.yaml` template with default value `resume.pdf`
- [ ] Implement default logic: if resume_path is empty/not set, use `resume.pdf` in project root
- [ ] Verify: resume_path loaded in config, defaults to resume.pdf if not set

### 3. Single LLM Resume Extraction
- [ ] Modify `src/job_hunter/resume/parser.py`:
  - Create `parse_resume_full(resume_path)` returning `(ResumeProfile, dict)`
  - Update existing `parse_resume()` to use new function
  - LLM prompt extracts both basic and detailed sections in one call
- [ ] Test: Single LLM call produces both basic and detailed data
- [ ] Verify: Pydantic validation for basic profile works

### 4. Load Functions for Profile + Detailed
- [ ] Implement `load_profile_with_detailed()` in `resume/parser.py`
  - Returns both basic profile and detailed profile together
  - For use wherever profile data is sent to LLM
- [ ] Update any existing code that loads profile to optionally load detailed too

### 4. Detailed Profile File Management
- [ ] Implement `save_detailed_profile(detailed_data)` in `resume/parser.py`
  - Save to `data/profile_detailed.yaml` with proper YAML formatting
- [ ] Implement `load_detailed_profile()` in `resume/parser.py`
  - Load from `data/profile_detailed.yaml`, return dict
- [ ] Verify: `profile_detailed.yaml` created with expected structure:
  - tech_experience
  - achievements
  - challenges_solved
  - interests
  - key_responsibilities
  - extracted_summary

### 5. Resume Change Detection
- [ ] Implement file hash comparison in `resume/parser.py`:
  - Calculate MD5/SHA256 of resume file
  - Store hash in profile.json or separate file
  - Compare on each run
- [ ] Alternative: Compare file modification time (mtime)
- [ ] Trigger regeneration if resume changed
- [ ] Verify: Changing resume file triggers regeneration of both profiles

### 6. Integration Test
- [ ] Run full pipeline: `job-hunter run --resume resume.pdf`
- [ ] Verify: `profile.json` created with basic profile
- [ ] Verify: `profile_detailed.yaml` created with detailed profile
- [ ] Run second time: verify cached profiles loaded (no LLM call)
- [ ] Change resume file, run third time: verify regeneration

### 7. Update Existing Code
- [ ] Update `src/job_hunter/graph/nodes.py`:
  - Load detailed profile for scoring context (if needed)
- [ ] Update any code that references old screening_answers location

### 8. Documentation
- [ ] Add Phase 2a entry to `specs/changelog/YYYY-MM.md`
- [ ] Update `specs/status.md` to show Phase 2a as planned

---

## Implementation Notes

- Single LLM call should extract basic + detailed in one prompt
- Profile detailed can be edited by user after generation
- Resume change detection uses file hash or mtime comparison
- Both profile.json and profile_detailed.yaml must be regenerated if resume changes
- Detailed profile stored alongside basic — available whenever profile data sent to LLM
- Default resume_path is `resume.pdf` in project root

---

## Testing Checklist

| Test | Expected Result |
|------|-----------------|
| First run with new parser | profile.json + profile_detailed.yaml created in single LLM call |
| Second run (no resume change) | Both loaded from cache, no LLM call |
| Third run (resume changed) | Both regenerated via single LLM call |
| Edit profile_detailed.yaml | Changes persist after regeneration (user section preserved) |
| Run with --force-parse | Force regeneration regardless of cache |

---

## Files Modified

| File | Change |
|------|--------|
| `config/user.yaml` | Remove screening_answers, add resume_path |
| `config/screening.yaml` | New file with screening_answers |
| `src/job_hunter/config/__init__.py` | Load screening.yaml, add ScreeningConfig, add resume_path |
| `src/job_hunter/resume/parser.py` | Single LLM call, save/load detailed profile, change detection |