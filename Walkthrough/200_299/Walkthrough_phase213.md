# Phase 213 Walkthrough

## Summary

Phase 213 created a new standalone `agent` surface named `Ops Pilot`, mounted it into the main app, and exposed it from the dashboard with a dedicated button above the existing AI Agent entry.

## What Changed

- Added a new mounted sub-app at `/agent`.
- Added a new lazy-loaded dashboard fragment at `/agent-panel`.
- Added new frontend assets under `/agent/static/`.
- Added a new dashboard button labeled `Open Ops Pilot`.
- Implemented direct lead CRUD APIs and a dedicated lead workspace UI for the new agent.
- Updated runtime docs and focused testing docs to reflect the new surface.

## Backup

- Targeted backups were created under `backups/200_299/phase213/` for the modified main-app, dashboard, and docs modules.

## Verification

- JavaScript syntax check:
  - `node --check development/agent/ui/frontend/static/js/app.js`
- Focused unit tests:
  - `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py -q`
- Result:
  - `9 passed`

## Notes

- This phase intentionally implemented a new agent surface without building on the existing AI Agent runtime code.
- The current standalone agent scope is lead CRUD only.
