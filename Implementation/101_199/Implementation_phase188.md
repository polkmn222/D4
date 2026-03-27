# Phase 188 Implementation

## Scope Executed

1. Confirmed the next shared phase number as `188`.
2. Backed up only the modified modules and files under `backups/101_199/phase188/`.
3. Aligned runtime and deployment entry paths with the active `development/` app root.
4. Updated canonical documentation and folder-local READMEs that still described the legacy `.gemini/development` layout.
5. Added automated coverage for runtime path alignment.
6. Removed all in-scope `GEMINI.md` files after backing them up.

## Changes Applied

### Runtime and Deployment

- Updated `api/index.py` so Vercel adds `development` to `sys.path`.
- Updated `run_crm.sh` so the app root resolves to `development/`.
- Updated `run_crm.sh` so a failed `open` call does not terminate startup verification.
- Updated `render.yaml` so Render uses `rootDir: development` and installs dependencies from `../requirements.txt`.
- Updated `pytest.ini` so pytest cache writes to `development/.pytest_cache`.
- Updated the path comments in `development/web/backend/app/main.py` to match the active structure.

### Tests

- Updated `development/test/unit/ai_agent/backend/test_ai_agent_lead_real_db_phase177_v2.py` to use the `development` app root.
- Added `development/test/unit/web/backend/test_runtime_path_alignment.py` to verify:
  - `api/index.py`
  - `run_crm.sh`
  - `render.yaml`
  - `pytest.ini`

### Documentation

- Updated canonical docs under `development/docs/` so runtime, workflow, deployment, and testing instructions point to `development/`.
- Updated folder-local README files under `development/ai_agent/`, `development/db/`, `development/web/backend/`, `development/web/frontend/`, and `development/web/message/` to match the current structure.

### Removed Files

- Deleted these files after backing them up:
  - `development/web/backend/app/api/GEMINI.md`
  - `development/web/backend/app/services/GEMINI.md`
  - `development/web/backend/app/utils/GEMINI.md`
  - `development/web/frontend/templates/GEMINI.md`

## Validation

- Focused unit test:
  - `PYTHONPATH=development pytest development/test/unit/web/backend/test_runtime_path_alignment.py -q`
  - Result: `4 passed`
- Full unit suite:
  - `PYTHONPATH=development pytest development/test/unit -rs -q`
  - Result: `34 failed, 72 passed, 1 warning`
- Runtime startup:
  - `./run_crm.sh`
  - Result: the app booted successfully under the aligned folder structure when database access was available.

## Risk Notes

- The full unit suite still has many pre-existing failures outside the path-alignment scope, concentrated in AI-agent behavior assertions, stale frontend path expectations, and a message-template CRUD expectation.
- `development/test/integration/test_e2e_simulation.py` still references legacy imports and a removed `SureMService` path. It was not changed in this phase because that file appears stale and requires a separate scoped review.
