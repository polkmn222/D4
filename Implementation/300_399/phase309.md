# Phase 309 Implementation

- Added failed-send audit recording to `MessagingService.send_message(...)`.
- When message dispatch fails before provider send or during provider rejection, D5 now creates a `MessageSend` row with `status="Failed"`.
- Avoided duplicate failed rows when the provider already returned an error response and a failed `MessageSend` row was already created.
- Added focused unit coverage for:
  - provider rejection creating a failed message row
  - pre-dispatch validation failure creating a failed message row
