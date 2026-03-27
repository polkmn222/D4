## Phase 190 Implementation

- Updated `development/docs/agent.md` with current AI Agent lookup-name behavior and messaging provider notes.
- Updated `development/docs/deployment.md` with current Slack/Solapi verification guidance, Solapi IP allowlist behavior, and MMS size rule separation.
- Updated `development/docs/testing/runbook.md`, `development/docs/testing/strategy.md`, and `development/docs/testing/known_status.md` with current executable commands and focused test references.
- Updated `development/test/docs/README.md` to mark it as archival and point to canonical testing docs.
- Added a mock-provider MMS unit test in `development/test/unit/messaging/test_messaging_flows.py`.
- Added runtime provider diagnostics through `/messaging/provider-status`.
- Added provider status helpers in `web/message/backend/services/message_providers/factory.py`.
- Added unit coverage for provider status warnings in `development/test/unit/web/message/backend/test_provider_status.py`.
- Ran real external provider verification:
  - Solapi MMS send attempt reached the provider but was rejected by Solapi IP allowlist enforcement.
  - Slack MMS-style notification send succeeded through the configured webhook.
