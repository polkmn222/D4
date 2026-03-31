Phase 307 walkthrough

Unit verification:

`PYTHONPATH=development pytest -m unit development/test/unit/messaging/test_surem_provider.py development/test/unit/web/message/backend/test_provider_status.py development/test/unit/web/message/backend/test_relay_dispatch_endpoint.py development/test/unit/web/message/backend/test_demo_relay_availability.py -q`

Result:

- `19 passed in 0.52s`

Real SureM SMS verification:

- Executed one fixed-recipient SMS send via `SuremMessageProvider`
- Result:
  - `status: success`
  - `provider: surem`
  - `code: A0000`
  - `message: SureM accepted the SMS request.`

Notes:

- The test used the fixed recipient and fixed reqPhone environment values already present in `development/.env`.
- LMS/MMS are still not wired in the SureM provider.
