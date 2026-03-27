# Phase 188 Walkthrough

## Summary

Phase 188 aligned the active repository with the current `development/` runtime root, preserved the affected modules in `backups/101_199/phase188/`, added automated path-alignment coverage, and removed the in-scope `GEMINI.md` files after backup.

## What Changed

### Runtime Path Alignment

- The Vercel shim in `api/index.py` now imports the app from the active `development/` root.
- `run_crm.sh` now targets `development/` instead of `.gemini/development`.
- `run_crm.sh` now treats GUI browser-launch failure as non-fatal.
- `render.yaml` now points Render at `development/` and uses the correct relative `requirements.txt` path.
- `pytest.ini` now uses `development/.pytest_cache`.

### Documentation Alignment

- Canonical docs under `development/docs/` now describe the active `development/` layout instead of the retired `.gemini/development` root.
- Folder-local README files for AI agent, database, backend, frontend, and messaging were updated to point to the active docs and test locations.

### Cleanup

- Removed these files after backup:
  - `development/web/backend/app/api/GEMINI.md`
  - `development/web/backend/app/services/GEMINI.md`
  - `development/web/backend/app/utils/GEMINI.md`
  - `development/web/frontend/templates/GEMINI.md`

## Verification

### Passed

- `PYTHONPATH=development pytest development/test/unit/web/backend/test_runtime_path_alignment.py -q`
- Elevated `./run_crm.sh` startup verification with database access

### Failed Outside Phase Scope

- Elevated full unit suite:
  - `PYTHONPATH=development pytest development/test/unit -rs -q`
  - Result: `34 failed, 72 passed, 1 warning`
- The failures are not introduced by the phase 188 path changes. They are dominated by:
  - AI-agent expectation mismatches in existing tests
  - stale frontend asset-path assumptions in `test_responsive_ui_css.py`
  - a message-template CRUD subject expectation mismatch

## Open Issues Reported, Not Auto-Fixed

1. `development/test/integration/test_e2e_simulation.py` still uses legacy `backend.app.*` imports and references `SureMService`, which does not match the active structure.
2. The canonical `known_status.md` full-suite reference is older than the currently observed elevated run and should be revised only when the broader failing suite is intentionally triaged.
3. Historical loose backup folders still exist directly under `backups/`, but phase 188 artifacts were stored in the grouped path as requested.
