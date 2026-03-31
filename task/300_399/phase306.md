Phase 306 task record

- Scope: SureM SMS-only relay send contract
- Changed modules:
  - `development/web/message/backend/services/message_providers`
  - `development/test/unit/messaging`
  - `development/test/unit/web/message/backend`
- Safety constraints kept:
  - fixed recipient only
  - fixed reqPhone only
  - LMS/MMS not implemented in SureM provider yet

