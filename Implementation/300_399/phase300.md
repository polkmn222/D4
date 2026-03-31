## Phase 300

- Fixed AI Agent `Change AI Recommend` follow-up so bare mode replies like `Hot Deals` continue the pending recommendation flow instead of falling into the out-of-scope guard.
- Added conversation context helpers for pending recommendation-mode changes.
- Updated AI Agent maximize styling so the default window stays at `90%` zoom and maximized mode uses `95%`.
- Improved AI Agent `Send Message` with no current selection to open `/messaging/ui` directly with a guided message instead of stopping with a plain clarification.
- Added backend and frontend unit coverage for the new recommendation follow-up, guided send-message entry, and maximize zoom contract.
