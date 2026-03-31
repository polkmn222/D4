# Phase 295 Task Record

## User Request
- Make all object flows more consistent.
- Opportunity:
  - required fields only `contact`, `name`, `stage`
  - hide `status`
  - open/edit/new should be unified
- Contact:
  - hide `status`
- Grouped objects (`brand`, `asset`, `product`, `template`) should continue to open flow after create/edit instead of generic success text.
- Remove top-scroll jump behavior.
- Verify open cards/actions across objects and add tests as needed.

## Work Done
- Repaired AI Agent inline web-form submit bridge so redirects resolve back into `OPEN_RECORD`.
- Hid opportunity/contact `status` from user-facing forms while preserving internal defaults.
- Relaxed edit validation by reusing existing required values from the record.
- Expanded opportunity open card details.
- Fixed grouped object edit route gaps.
- Added/updated unit and DOM tests for the new contracts.

## Notes
- Manual testing was not performed.
- SQLite was not used.
