Phase 306 walkthrough

Implemented the SureM SMS request shape with fixed safety numbers and verified by unit tests only.

Executed:

`PYTHONPATH=development pytest -m unit development/test/unit/messaging/test_surem_provider.py development/test/unit/web/message/backend/test_provider_status.py -q`

Result:

- `12 passed in 0.30s`

Notes:

- `to` is forced from `SUREM_FORCE_TO_NUMBER`.
- `reqPhone` is forced from `SUREM_REQ_PHONE`.
- Non-SMS types return an explicit error until later phases add LMS/MMS support.
