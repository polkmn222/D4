# Phase 220 Walkthrough

## Goal

Restore shared web lookup behavior inside the standalone `Ops Pilot` lead workspace.

## What Changed

- `Ops Pilot` now opens `/leads/embedded-form` instead of a bare `/leads/new-modal` fragment.
- The new embedded lead page loads shared web assets, including `lookup.js`.
- That page includes the shared `sf_form_modal.html` lead form so field and lookup rendering still come from the existing web form contract.

## Why

- The modal fragment alone does not carry the shared lookup JavaScript and CSS it depends on.
- The main web runtime works because those assets already exist in the parent page.
- The embedded page gives the iframe its own complete lookup runtime without forking the lead form.

## Validation

- `node --check development/agent/ui/frontend/static/js/app.js`
- `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py development/test/unit/web/backend/app/api/test_form_router_modals.py -q`
