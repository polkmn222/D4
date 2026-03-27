# Phase 220 Implementation

## Summary

Phase 220 replaces the standalone agent's bare lead modal fragment iframe target with a dedicated embedded lead page that loads the shared web lookup assets.

## Changes

- Pointed `Ops Pilot` lead create/edit to `/leads/embedded-form`.
- Added a dedicated embedded lead page template that loads shared web CSS and `lookup.js`.
- Kept the shared lead form template as the source of truth by including `templates/sf_form_modal.html` inside the embedded page.
- Added a dedicated router path for the embedded lead page.
- Updated focused unit tests and docs for the embedded full-page contract.

## Modified Files

- `development/agent/ui/frontend/static/js/app.js`
- `development/web/backend/app/api/form_router.py`
- `development/web/frontend/templates/leads/embedded_form_page.html`
- `development/test/unit/agent/test_frontend_contract.py`
- `development/test/unit/web/backend/app/api/test_form_router_modals.py`
- `development/docs/agent.md`
- `development/docs/testing/known_status.md`

## Verification Plan

- Validate standalone agent frontend JavaScript syntax.
- Run focused standalone agent and web embedded-form unit tests.
