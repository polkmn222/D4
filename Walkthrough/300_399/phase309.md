# Phase 309 Walkthrough

## What changed

- `MessagingService.send_message(...)` now keeps a best-effort failure audit path.
- If dispatch fails before provider send, the service writes a `MessageSend` row with `status="Failed"` and re-raises the error.
- If the provider returns an error response, the existing failed row is preserved and no duplicate failure row is created.

## Verification

- Command:
  - `PYTHONPATH=development pytest -m unit development/test/unit/web/message/backend/test_message_send_limits.py development/test/unit/messaging/test_surem_provider.py development/test/unit/web/message/backend/test_relay_dispatch_endpoint.py development/test/unit/web/message/backend/test_demo_relay_availability.py development/test/unit/web/message/backend/test_message_template_modal_submission.py -q`
- Result:
  - `28 passed in 0.53s`

## Notes

- This phase does not prove why a specific LMS/MMS attempt failed at carrier level.
- It does ensure D5 records failed attempts so the Send object/history is visible even when delivery does not complete.
