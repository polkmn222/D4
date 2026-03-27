# Phase 222 Walkthrough

## Goal

Make `Ops Pilot` transitions feel smoother by removing the temporary web detail flash and keeping the latest workspace content in view.

## What Changed

- The embedded iframe now enters a pending hidden state before form reloads and save redirects.
- When the iframe settles on the embedded lead form route, it becomes visible again.
- When a save completes, the iframe stays hidden and the post-save open card takes over.
- The standalone main workspace now scrolls downward automatically as new interaction states appear.

## Why

- The iframe briefly rendering `/leads/{id}` before the post-save card caused a visible flash of the web detail tabs.
- The standalone shell also felt static because the newest workspace state could sit out of view.
- Hiding transitions and scrolling toward the latest state makes the flow behave more like a conversation surface.

## Validation

- `node --check development/agent/ui/frontend/static/js/app.js`
- `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py development/test/unit/web/backend/app/api/test_form_router_modals.py -q`
