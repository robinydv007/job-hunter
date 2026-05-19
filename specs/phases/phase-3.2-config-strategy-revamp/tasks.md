# Phase 3.2 — Tasks: Config Strategy Revamp

> **Status: COMPLETE** — End-to-end pipeline test passed (2026-04-23)

## Task Checklist

### 3.2a — Schema + Bootstrap Foundation
- [x] Define final schemas in `src/job_hunter/config/__init__.py`
  - [x] Add `AppConfig` for `app.yaml`
  - [x] Add `UserConfig` for `user.yaml`
  - [x] Add `PlatformConfig` for `platform.yaml`
  - [x] Add `ProfileCache` / `ResumeProfile` for `data/profile_cache.json`
  - [x] Add template/model helpers for each file type
- [x] Finalize per-field blank semantics
  - [x] `null` for nullable scalars
  - [x] `[]` for empty lists
  - [x] `{}` for empty mappings
- [x] Add bootstrap helpers
  - [x] `ensure_config_files_exist()`
  - [x] `create_app_template()`
  - [x] `create_user_template()`
  - [x] `create_platform_template()`
  - [x] `seed_user_config_from_resume()` for missing user config only
- [x] Update `src/job_hunter/cli.py`
  - [x] Bootstrap missing config on `init`
  - [x] Bootstrap missing config on `run`
  - [x] Skip writing files that already exist
  - [x] Keep existing config files untouched when validating

### 3.2b — Runtime Migration
- [x] Update `src/job_hunter/config/__init__.py`
  - [x] Add layered loaders for app/user/platform configs
  - [x] Merge into a single effective runtime config
  - [x] Expose platform override resolution explicitly
- [x] Seed `user.yaml` from resume data when missing
  - [x] Use `data/profile_cache.json` if available
  - [x] Never overwrite existing user values
- [x] Refactor runtime consumers
  - [x] `graph/nodes.py`
  - [x] `search/naukri.py`
  - [x] `scoring/engine.py`
  - [x] `scoring/llm_scorer.py`
  - [x] `apply/naukri_apply.py`
  - [x] `export/csv_export.py`
  - [x] `resume/schema.py`
  - [x] `graph/workflow.py`
- [x] Ensure platform overrides win over app defaults
- [x] Remove assumptions about current `profile` / `screening` layout
  - [x] Remove direct reads of old config fields in runtime paths

### 3.2c — Validation + Cleanup
- [x] Add migration support for existing installs (backward compat layer in `load_app_config()`)
- [x] Add tests (`tests/test_config.py` — 33 tests, all passing)
  - [x] Missing-file bootstrap
  - [x] Non-overwrite behavior
  - [x] Precedence and defaults
  - [x] Resume seeding behavior
  - [x] Role-family and platform overrides
  - [x] CSV export stability
- [x] Add migration/docs updates
  - [x] New config file responsibilities (documented in changelog 2026-04)
  - [x] Bootstrap behavior on init/run
  - [x] Empty value semantics
- [x] Update docs and migration notes (phase overview + history updated)
