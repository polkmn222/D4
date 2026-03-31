# Phase 332 Walkthrough

## What Changed

The AI Agent could open `brand`, `model`, `asset`, and `message_template` edit forms in chat, but the inline-save bridge only treated `lead`, `contact`, and `opportunity` as AI-managed submit targets. That meant grouped-object edit forms did not consistently complete with the same in-chat save continuity.

Phase 332 extends the AI-managed submit bridge to:

- recognize the grouped-object edit/create modal routes
- submit grouped-object values through the AI Agent form-submit API
- return refreshed `OPEN_RECORD` continuity on success
- keep message-template file-upload edits on the existing multipart web fallback path when a new file is selected

This keeps the existing web modal layout and field-order behavior while aligning save continuity with the AI Agent chat flow.

## Verification

- `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py -q`
- Result: `47 passed`
- `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
- Result: `76 passed`

## Not Run

- Manual browser verification was not run by policy.
