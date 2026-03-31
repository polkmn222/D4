Phase 286 Implementation

- Centralized Send Message recipient select-all behavior around the template-level selection API.
- Updated the header checkbox to call the shared `toggleSelectAll(...)` owner directly.
- Made `Messaging.recipients` delegate visible-row, sync, filter, and toggle work to the shared recipient API when present.
