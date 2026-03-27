# Phase 218 Walkthrough

## Goal

Stop the standalone `Ops Pilot` lead workspace from expanding around the embedded web form and make the form navigable through internal scrolling.

## What Changed

- Removed the iframe document-height auto-grow logic.
- Kept the workspace shell fixed inside the `Ops Pilot` layout.
- Allowed the embedded lead iframe to occupy the available shell height and scroll internally.

## Why

- A growing iframe made the whole agent surface feel oversized and unstable.
- The user wanted the lead form to behave like a contained workspace with its own scrolling area.
- A fixed shell keeps the agent UI predictable while preserving access to the full web lead form.

## Validation

- `node --check development/agent/ui/frontend/static/js/app.js`
- `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py -q`
