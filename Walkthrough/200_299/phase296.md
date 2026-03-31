# Phase 296 Walkthrough

## Verification
- Command:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_phase278_query_and_recommend_contract.py -q`
- Result:
  - `73 passed`

## Outcome
- Home and AI Agent now use the same sendable recommendation source.
- Home and AI Agent now share the same dashboard recommendation limit of 4.
