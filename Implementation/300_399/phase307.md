Phase 307 implementation

- Switched the relay default target from `solapi` to `surem`.
- Updated relay health and provider-status logic to validate SureM environment variables by default.
- Added support for existing `.env` aliases:
  - `SUREM_AUTH_userCode`
  - `SUREM_AUTH_secretKey`
  - `SUREM_TO`
  - `SUREM_reqPhone`
  - `SUREM_AUTH_URL`
  - `SUREM_SMS_URL`
- Verified a real fixed-number SureM SMS request returned success from the provider.

