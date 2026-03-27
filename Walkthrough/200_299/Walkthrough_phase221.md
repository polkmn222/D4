# Phase 221 Walkthrough

## Goal

Make the standalone `Ops Pilot` lead flow feel closer to the AI Agent by showing an open-record card after save and simplifying the embedded form footer.

## What Changed

- Added a record-card slot to the standalone lead workspace.
- When the embedded lead form saves and redirects to the lead detail route, the shell now fetches lead detail data and renders an AI Agent-style summary card.
- The card provides Open Record, Edit, and Delete actions.
- The embedded footer now shows Cancel instead of Save & New, and Cancel returns control to the standalone shell.

## Why

- After save, the embedded form no longer needs to remain the primary surface.
- The AI Agent record card is a clearer post-save state for review and next actions.
- `Save & New` adds little value inside the standalone shell compared with a direct cancel action.

## Validation

- `node --check development/agent/ui/frontend/static/js/app.js`
- `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py development/test/unit/web/backend/app/api/test_form_router_modals.py -q`
