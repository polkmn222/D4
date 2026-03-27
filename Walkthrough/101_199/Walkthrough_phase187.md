# Phase 187: Send Message MMS & Placeholder Enhancement Walkthrough

## Objective
The objective was to fix broken MMS image previews in the "Send Message" tab and enhance both the frontend preview and backend delivery with real-time placeholder substitution for subject lines and message content.

## Changes Made

### 1. MMS Image Fix
- **Folder Migration**: Renamed the internal storage folder from `uploads/templates` to `uploads/message_templates` to match the current Phase 186/187 naming convention.
- **Resilient Path Resolution**: 
  - Updated the `messaging_ui` router to automatically rewrite old template paths (`/static/uploads/templates/`) to the new location during UI rendering.
  - Updated `MessagingService._resolve_image_url` to perform the same migration for outgoing MMS messages, ensuring that even if a database record still points to the old path, the image is correctly resolved and sent.

### 2. Placeholder Substitution Enhancement
- **Frontend Preview**: 
  - Updated `updatePreview()` in `send_message.html` to perform real-time substitution of `{name}`, `{customer_name}`, and `{model}` placeholders.
  - The preview now uses the data from the first selected recipient to show exactly how the message will look to the customer.
  - Added event listeners to recipient checkboxes so that changing the selection immediately updates the preview.
- **Subject Support**: 
  - Enabled placeholder substitution for the **Subject** line in the frontend preview bubble.
  - Updated `MessagingService` backend to support `{customer_name}` as an alias for `{name}` in both content and subject.

### 3. Code Cleanup
- Removed redundant variable declarations in `send_message.html`'s `applyTemplate` function.

## Verification
- Verified that renaming the folder and adding migration logic fixes the broken image icons in the screenshot.
- Verified that typing `{customer_name}` or `{model}` in the content or subject area results in correct data substitution in the mobile preview bubble when a recipient is selected.
- Verified that outgoing messages via the backend correctly handle the new aliases and path migration.

## Backup
- Key files were backed up in previous turns or are modified in-place with `replace` tool safely.
