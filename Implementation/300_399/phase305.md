Phase 305 implementation

- Added a new `SuremMessageProvider` that supports:
  - `SUREM_USER_CODE`
  - `SUREM_SECRET_KEY`
  - access-token retrieval from `https://rest.surem.com/api/v1/auth/token`
  - in-memory token cache reuse before expiry
- Registered `surem` in `MessageProviderFactory`.
- Extended provider status output to expose SureM credential configuration.
- Kept actual SureM send delivery out of this phase because only the auth/token contract was provided.

