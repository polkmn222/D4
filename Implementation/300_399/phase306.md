Phase 306 implementation

- Extended `SuremMessageProvider` to support the documented SureM SMS send endpoint:
  - `POST /api/v1/send/sms`
- Enforced safety constraints for this phase:
  - `SUREM_FORCE_TO_NUMBER` is required and used as the fixed recipient
  - `SUREM_REQ_PHONE` is required and used as the fixed sender/request phone
  - only `SMS` is supported in this phase
  - SMS content is truncated to 90 bytes before dispatch
- Updated provider status to expose fixed-recipient and req-phone configuration.

