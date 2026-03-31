# Phase 311 Walkthrough

## What changed

- `MessageSend` now stores the actual message type, subject, attachment, and image URL.
- Runtime bootstrap adds those columns automatically for existing databases.
- The send flow now writes those fields when creating a `MessageSend` row.
- Message detail pages now render the saved image directly.

## Verification

- Command:
  - `PYTHONPATH=development pytest -m unit development/test/unit/web/message/backend/test_message_send_model_contract.py development/test/unit/web/message/backend/test_message_send_limits.py development/test/unit/web/message/backend/test_message_template_modal_submission.py -q`
- Result:
  - `20 passed in 0.48s`
