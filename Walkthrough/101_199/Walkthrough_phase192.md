## Phase 192 Walkthrough

### Summary

This phase introduces a relay delivery path so the local runtime can keep direct Solapi delivery while Vercel can demonstrate live sending without requiring Vercel outbound IP allowlisting.

### What Changed

- Added `relay` as a first-class messaging provider.
- Added `/messaging/relay-dispatch` with bearer-token protection.
- Updated provider status reporting to surface relay configuration.
- Updated deployment guidance for:
  - local direct `solapi`
  - Vercel `relay`
  - Render relay target runtime

### Verification Plan

Run focused messaging unit tests only:

```bash
DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest \
  development/test/unit/messaging/test_relay_provider.py \
  development/test/unit/web/message/backend/test_relay_dispatch_endpoint.py \
  development/test/unit/web/message/backend/test_provider_status.py \
  development/test/unit/messaging/test_messaging_flows.py \
  development/test/unit/web/message/backend/test_message_template_limits.py \
  development/test/unit/web/message/backend/test_message_send_limits.py -q
```

### Operating Mode

- Local testing:
  - `MESSAGE_PROVIDER=solapi`
- Vercel demo:
  - `MESSAGE_PROVIDER=relay`
  - `RELAY_MESSAGE_ENDPOINT=https://<render-service>/messaging/relay-dispatch`
- Relay runtime:
  - `MESSAGE_PROVIDER=solapi`
  - `RELAY_MESSAGE_TOKEN=<shared secret>`
  - `RELAY_TARGET_PROVIDER=solapi`
