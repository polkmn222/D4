Phase 308 walkthrough

Automated verification:

`PYTHONPATH=development pytest -m unit development/test/unit/messaging/test_surem_provider.py development/test/unit/web/message/backend/test_provider_status.py development/test/unit/web/message/backend/test_relay_dispatch_endpoint.py development/test/unit/web/message/backend/test_demo_relay_availability.py development/test/unit/web/message/backend/test_message_template_modal_submission.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py -q`

Result:

- `74 passed in 3.12s`

Real fixed-number provider verification:

- LMS result:
  - `status: success`
  - `provider: surem`
  - `code: A0000`
- MMS result:
  - `status: success`
  - `provider: surem`
  - `code: A0000`

Notes:

- The MMS test used `development/web/app/static/uploads/message_templates/25f73140-29e2-4749-b980-829b00b62ae9.jpg`
- Web/AI Agent now use the admin-contact message when demo/relay availability is not ready.
