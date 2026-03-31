Phase 304 walkthrough

Changes verified with unit and DOM-oriented source-contract tests only.

Executed:

`PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py development/test/unit/web/message/backend/test_message_template_modal_submission.py -q`

Result:

- `62 passed in 3.28s`

Notes:

- AI Agent debug toggle is present again and persists via local storage.
- AI Agent Send Message base payload no longer includes recommended recipients.
- AI recommendations are loaded separately from `/messaging/recommendations` on demand.
- Web Send Message exposes `Save Recipients` and `Clear All`.
