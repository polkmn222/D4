## Phase 328 Walkthrough

### Verification

- Ran unit tests:
  - `PYTHONPATH=development pytest -m unit development/test/unit/web/message/backend/test_message_template_modal_submission.py development/test/unit/web/backend/app/api/test_form_router_modals.py development/test/unit/web/message/backend/test_message_template_image_routes.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_quick_guide_contract.py -q`
  - Result: `78 passed`
- Ran non-phase1 AI Agent object contract tests:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase287_multi_object_contract.py development/test/unit/ai_agent/backend/test_phase269_multi_object_deterministic.py -q`
  - Result: `16 passed`
- Attempted targeted CRUD service tests for `asset`, `model`, and `message_template`:
  - `PYTHONPATH=development pytest development/test/unit/crm/test_core_crud.py::test_asset_crud development/test/unit/crm/test_core_crud.py::test_model_crud development/test/unit/crm/test_core_crud.py::test_message_template_crud -q`
  - Result: blocked by environment DNS resolution failure against the configured remote PostgreSQL host
- No manual testing was performed.
- No SQLite was used.

### Notes

- The AI Agent template form visibility issue was caused by `/new-modal` extraction dropping the shared modal script that controls `record_type`-based field visibility.
- The AI Agent search mismatch issue was caused by filtering against serialized row JSON instead of visible table columns.
