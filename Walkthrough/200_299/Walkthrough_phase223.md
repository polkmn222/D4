# Phase 223 Walkthrough

## Goal

Fix the standalone `Ops Pilot` loader so New/Edit forms show up reliably even when the browser fires an initial iframe bootstrap load.

## What Changed

- The iframe load handler now ignores `about:blank` bootstrap loads.
- Pending state remains active during the bootstrap pass and only resolves on a real embedded lead route.
- If the iframe load handler falls into its error path, pending state is now released so the workspace does not stay hidden forever.
- Focused frontend tests now assert the bootstrap guard, pending release, and embedded-form visibility contract.

## Why

- Some browsers fire an initial iframe `about:blank` load before the target page.
- Without guarding that bootstrap event, the standalone shell could leave the embedded form hidden behind the pending class.
- The stronger tests lock this loader state machine so New/Edit stays visible.

## Validation

- `node --check development/agent/ui/frontend/static/js/app.js`
- `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py development/test/unit/web/backend/app/api/test_form_router_modals.py -q`
