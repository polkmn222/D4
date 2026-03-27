# Phase 219 Walkthrough

## Goal

Make lead lookup fields usable in the standalone `Ops Pilot` workspace without diverging from the shared web lead form.

## What Changed

- Added `embedded=1` support to the shared lead form route.
- The shared form template now renders without the modal close control and without modal body height clipping when embedded.
- `Ops Pilot` now opens `/leads/new-modal?embedded=1` for lead create/edit.

## Why

- The standalone agent should not maintain its own custom lead lookup behavior.
- The shared web lead form is already the source of truth for lead fields and lookup initialization.
- Embedded mode keeps that shared contract while removing modal-only UI behavior that does not fit the agent shell.

## Validation

- `node --check development/agent/ui/frontend/static/js/app.js`
- `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py development/test/unit/web/backend/app/api/test_form_router_modals.py -q`
