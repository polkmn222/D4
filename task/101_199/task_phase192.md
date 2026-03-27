## Phase 192 Task

### Goal

Enable message delivery from both local development and Vercel demo environments without requiring Vercel to call Solapi directly.

### Scope

- Add a relay message provider for Vercel-safe delivery handoff.
- Add a protected relay dispatch endpoint on the shared backend.
- Keep local development able to use direct `solapi`.
- Update deployment documentation for Render relay runtime and Vercel relay caller setup.
- Add unit tests for relay provider behavior and relay endpoint behavior.

### Constraints

- No manual testing.
- Do not broaden changes outside the messaging module and deployment docs.
- Preserve the existing Solapi guard on Vercel direct delivery.

### Expected Result

- Local runtime can keep `MESSAGE_PROVIDER=solapi`.
- Vercel runtime can use `MESSAGE_PROVIDER=relay`.
- The relay runtime can authenticate requests and forward to `solapi`.
