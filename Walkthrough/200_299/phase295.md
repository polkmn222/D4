# Phase 295 Walkthrough

## Verification
- Focused suites:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/web/frontend/test_ui_js_logic.py -q`
  - Result: `118 passed`
- Broader regression:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/backend/test_phase269_multi_object_deterministic.py development/test/unit/ai_agent/backend/test_phase279_noisy_alias_and_clarification_contract.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_phase278_query_and_recommend_contract.py development/test/unit/web/frontend/test_ui_js_logic.py -q`
  - Result: `132 passed`

## Behavioral Outcomes
- Opportunity/contact forms no longer surface `status`.
- Opportunity create/edit validates against `contact`, `name`, `stage`.
- Edit save can reuse existing hidden required values.
- Inline web forms inside AI Agent now resolve back into chat `OPEN_RECORD` continuity instead of generic success text.
- Message template open cards now expose edit/delete actions.
- Grouped object edit routing is aligned for brand/template.

## Remaining Constraints
- Verification is unit/DOM only.
- No manual/browser verification was performed per project rules.
