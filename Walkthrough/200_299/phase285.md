Phase 285 Verification

- Verified `OPEN_FORM` source contract and lead form layout metadata.
- Verified jump-button DOM behavior for off-bottom and at-bottom states.
- Verified delete success copy removes raw IDs for model and lead-aligned objects.

Tests:
- `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_lead_crud_module.py development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/backend/test_phase275_missing_record_labels.py development/test/unit/ai_agent/backend/test_phase285_lead_contract.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/web/frontend/test_phase276_loading_and_list_view_contract.py -q`
