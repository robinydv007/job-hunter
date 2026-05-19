# Phase 3.2 — Plan: Config Strategy Revamp

## 3.2a. Schema + Bootstrap Foundation
- Freeze the final YAML contract in `src/job_hunter/config/__init__.py`.
- Introduce explicit models for:
  - `AppConfig` from `config/app.yaml`
  - `UserConfig` from `config/user.yaml`
  - `PlatformConfig` from `config/platform.yaml`
  - `ProfileCache` / `ResumeProfile` from `data/profile_cache.json`
- Make every optional value nullable or empty-collection friendly.
- Standardize blank semantics:
  - scalar fields: `null`
  - list fields: `[]`
  - mapping fields: `{}`
- Add bootstrap helpers in `src/job_hunter/config/bootstrap.py` or `config/__init__.py`.
- Implement `ensure_config_files_exist(project_root, resume_path=None)`.
- Implement `create_app_template()` / `create_user_template()` / `create_platform_template()` helpers.
- Seed only safe fields from resume-derived data when `config/user.yaml` is missing.
- Never overwrite existing files; guard with `Path.exists()` before write.

### Deliverables
- New config models and loaders compiled cleanly.
- Bootstrap helpers available for CLI and runtime.
- Missing-file generation works without mutating existing files.

### File Order
1. `src/job_hunter/config/__init__.py`
2. `src/job_hunter/resume/parser.py`
3. `src/job_hunter/cli.py`
4. `src/job_hunter/resume/schema.py` only if cache shape needs adjustment

## 3.2b. Runtime Migration
- Refactor `load_config()` into layered loaders:
  - `load_app_config()`
  - `load_user_config()`
  - `load_platform_config()`
- Add a `build_effective_config()` merge step that resolves precedence.
- Keep `data/profile_cache.json` as a read-only input to the merge.
- Ensure `run` and `init` call bootstrap before config validation.
- Update runtime consumers:
  - `src/job_hunter/graph/nodes.py`
  - `src/job_hunter/search/naukri.py`
  - `src/job_hunter/scoring/engine.py`
  - `src/job_hunter/scoring/llm_scorer.py`
  - `src/job_hunter/apply/naukri_apply.py`
  - `src/job_hunter/export/csv_export.py`
  - `src/job_hunter/cli.py`
- Ensure platform overrides sit above app defaults.
- Remove assumptions about current `profile` / `screening` layout.

### Deliverables
- All runtime consumers read the new config model.
- Search/scoring/apply use the new sections directly.
- Platform-specific overrides are resolved in one place.

### File Order
1. `src/job_hunter/config/__init__.py`
2. `src/job_hunter/graph/nodes.py`
3. `src/job_hunter/search/naukri.py`
4. `src/job_hunter/scoring/engine.py`
5. `src/job_hunter/scoring/llm_scorer.py`
6. `src/job_hunter/apply/naukri_apply.py`
7. `src/job_hunter/export/csv_export.py`
8. `src/job_hunter/graph/workflow.py`

## 3.2c. Validation + Cleanup
- Add migration support for the new config layout.
- Add tests for missing-file bootstrap on `init` and `run`.
- Add tests that existing files are left untouched.
- Add tests for precedence: platform > app > user > cache > defaults.
- Add tests for blank/null/empty collection handling.
- Add tests that resume seeding only fills absent fields.
- Add tests for role-family scoring and screening overrides.
- Add tests for CSV export stability.
- Finalize migration notes and docs.

### Deliverables
- Regression coverage for bootstrap, precedence, and seeding.
- Docs updated to reflect final file contract.
- No remaining reliance on old config shape in production code.

### Exit Criteria
- New config files can be generated on demand.
- Existing config files are preserved.
- Search/scoring/apply/screening run against the new schema.
- Tests cover the main precedence and bootstrap paths.
