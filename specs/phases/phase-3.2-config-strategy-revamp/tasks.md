# Phase 3.2 — Tasks: Config Strategy Revamp

> **Status: NOT STARTED** — Awaiting design approval

## Task Checklist

### 3.2a — Schema + Bootstrap Foundation
- [ ] Define final schemas in `src/job_hunter/config/__init__.py`
  - [ ] Add `AppConfig` for `app.yaml`
  - [ ] Add `UserConfig` for `user.yaml`
  - [ ] Add `PlatformConfig` for `platform.yaml`
  - [ ] Add `ProfileCache` / `ResumeProfile` for `data/profile_cache.json`
  - [ ] Add template/model helpers for each file type
- [ ] Finalize per-field blank semantics
  - [ ] `null` for nullable scalars
  - [ ] `[]` for empty lists
  - [ ] `{}` for empty mappings
- [ ] Add bootstrap helpers
  - [ ] `ensure_config_files_exist()`
  - [ ] `create_app_template()`
  - [ ] `create_user_template()`
  - [ ] `create_platform_template()`
  - [ ] `seed_user_config_from_resume()` for missing user config only
- [ ] Update `src/job_hunter/cli.py`
  - [ ] Bootstrap missing config on `init`
  - [ ] Bootstrap missing config on `run`
  - [ ] Skip writing files that already exist
  - [ ] Keep existing config files untouched when validating

### 3.2b — Runtime Migration
- [ ] Update `src/job_hunter/config/__init__.py`
  - [ ] Add layered loaders for app/user/platform configs
  - [ ] Merge into a single effective runtime config
  - [ ] Expose platform override resolution explicitly
- [ ] Seed `user.yaml` from resume data when missing
  - [ ] Use `data/profile_cache.json` if available
  - [ ] Never overwrite existing user values
- [ ] Refactor runtime consumers
  - [ ] `graph/nodes.py`
  - [ ] `search/naukri.py`
  - [ ] `scoring/engine.py`
  - [ ] `scoring/llm_scorer.py`
  - [ ] `apply/naukri_apply.py`
  - [ ] `export/csv_export.py`
  - [ ] `resume/schema.py`
  - [ ] `graph/workflow.py`
- [ ] Ensure platform overrides win over app defaults
- [ ] Remove assumptions about current `profile` / `screening` layout
  - [ ] Remove direct reads of old config fields in runtime paths

### 3.2c — Validation + Cleanup
- [ ] Add migration support for existing installs
- [ ] Add tests
  - [ ] Missing-file bootstrap
  - [ ] Non-overwrite behavior
  - [ ] Precedence and defaults
  - [ ] Resume seeding behavior
  - [ ] Role-family and platform overrides
  - [ ] CSV export stability
- [ ] Add migration/docs updates
  - [ ] New config file responsibilities
  - [ ] Bootstrap behavior on init/run
  - [ ] Empty value semantics
- [ ] Update docs and migration notes
