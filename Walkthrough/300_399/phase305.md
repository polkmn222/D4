Phase 305 walkthrough

Implemented and verified SureM auth scaffolding only.

Executed:

`PYTHONPATH=development pytest -m unit development/test/unit/messaging/test_surem_provider.py development/test/unit/web/message/backend/test_provider_status.py development/test/unit/messaging/test_relay_provider.py -q`

Result:

- `12 passed in 0.33s`

Notes:

- SureM token retrieval is cached in memory until shortly before expiry.
- The provider currently returns an explicit auth-configured-but-send-not-wired message.
- Actual SureM message delivery requires the send API contract/endpoints in a later phase.
