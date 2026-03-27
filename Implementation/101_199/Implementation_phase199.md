# Phase 199 Implementation Plan

## Planned Changes

1. Preserve the full modal form element when the AI Agent loads `/new-modal` content.
2. Keep AI Agent inline form submission aligned with the web modal CRUD response contract.
3. Add focused tests that guard against stripping the form wrapper and verify the save-to-open source contract.

## Verification

- `PYTHONPATH=development DATABASE_URL=sqlite:///:memory: pytest development/test/unit/ai_agent/backend/test_lead_crud_module.py development/test/unit/web/message/backend/test_message_template_modal_submission.py -q`
