# Phase 187: Send Message MMS & Placeholder Enhancement

## Tasks
- [x] Fix broken MMS image preview in Send Message tab:
    - [x] Rename `uploads/templates` folder to `uploads/message_templates` for consistency.
    - [x] Add path migration logic in `messaging_ui` router to handle old template paths.
    - [x] Add path migration logic in `MessagingService._resolve_image_url`.
- [x] Enhance frontend preview with real-time placeholder substitution:
    - [x] Update `updatePreview()` in `send_message.html` to substitute `{name}`, `{customer_name}`, and `{model}`.
    - [x] Ensure subject line also supports placeholder substitution in both backend and frontend preview.
    - [x] Trigger `updatePreview()` when recipient selection changes.
- [x] Clean up redundant code in `send_message.html`.
- [x] Finalize documentation (Task, Walkthrough).
