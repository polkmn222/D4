Phase 305 task record

- Scope: relay target prerequisite setup for SureM auth only
- Changed modules:
  - `development/web/message/backend/services/message_providers`
  - `development/test/unit/messaging`
  - `development/test/unit/web/message/backend`
- Explicitly not changed in this phase:
  - live SureM SMS/LMS/MMS send endpoint wiring
  - relay runtime default target switch
  - deployment docs

