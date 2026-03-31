# Phase 311 Implementation

- Added message delivery metadata fields to `MessageSend`:
  - `subject`
  - `record_type`
  - `image_url`
  - `attachment_id`
- Added runtime column bootstrap for the new `message_sends` columns.
- Updated `MessagingService.send_message(...)` to persist the actual sent type, subject, attachment, and image URL into `MessageSend`.
- Updated message list/detail rendering to use saved message metadata instead of relying only on the template.
- Updated the message detail view to render the saved image directly when present.
