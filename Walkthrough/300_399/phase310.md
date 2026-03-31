# Phase 310 Walkthrough

## Findings

- The web Send Message screen did reach `/messaging/bulk-send` during the reported attempts.
- This was confirmed from `development/crm.log`, which showed repeated `POST /messaging/bulk-send HTTP/1.1 200 OK`.
- That means the issue is not simply “the UI never tried to send”.

## What changed

- Added source-contract tests that pin the web Send Message flow to forward:
  - `record_type`
  - `subject`
  - `attachment_id`
- Added tests that pin the MMS validation rule:
  - MMS requires attachment
  - LMS does not require attachment
- Updated the SureM provider status warning string so diagnostics match the current implementation.

## Verification

- Command:
  - `PYTHONPATH=development pytest -m unit development/test/unit/web/frontend/test_phase276_loading_and_list_view_contract.py development/test/unit/web/message/backend/test_provider_status.py development/test/unit/web/message/backend/test_message_send_limits.py development/test/unit/messaging/test_surem_provider.py development/test/unit/web/message/backend/test_relay_dispatch_endpoint.py development/test/unit/web/message/backend/test_demo_relay_availability.py development/test/unit/web/message/backend/test_message_template_modal_submission.py -q`
- Result:
  - `43 passed in 0.52s`
