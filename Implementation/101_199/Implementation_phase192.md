## Phase 192 Implementation

### Messaging Relay

- Added `RelayMessageProvider` to forward delivery payloads to a protected relay endpoint with bearer-token authentication.
- Extended `MessageDispatchPayload` with `to_dict()` to standardize payload handoff between provider layers.
- Added `MessageProviderFactory.get_provider_by_name()` so the relay runtime can dispatch to a target provider explicitly.
- Added `POST /messaging/relay-dispatch` to accept authenticated relay requests and forward them to `RELAY_TARGET_PROVIDER`.

### Runtime Guard

- Kept direct Solapi delivery blocked on Vercel unless `ALLOW_SOLAPI_ON_VERCEL=true`.
- Ensured the relay runtime can still dispatch to Solapi explicitly without tripping the default Vercel guard path.
- Fixed the failed-send error message path in `MessagingService.send_message()` to report the actual provider name safely.

### Deployment

- Updated `render.yaml` to expose relay-related environment variables.
- Updated deployment documentation to describe:
  - local direct Solapi sends
  - Vercel relay sends
  - Render relay target configuration
  - shared secret setup for relay authentication

### Test Coverage

- Added relay provider unit tests.
- Added relay dispatch endpoint unit tests.
- Updated message send limit tests for the factory dispatch refactor.
