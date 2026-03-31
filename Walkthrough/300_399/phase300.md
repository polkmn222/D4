## Phase 300 Walkthrough

1. Added `pending_recommendation_mode` context helpers so `Change AI Recommend` can safely accept a follow-up like `Hot Deals` on the next turn.
2. Updated recommendation resolution to treat those follow-ups as `MODIFY_UI`, then clear the pending state once the mode is set.
3. Changed the AI Agent no-selection `Send Message` path to open the messaging workspace directly with a guided instruction string.
4. Adjusted CSS so only maximized AI Agent uses `zoom: 0.95`; the base window remains `zoom: 0.9`.

### Verification

- `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
  - `72 passed`
- `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py -q`
  - `39 passed`
