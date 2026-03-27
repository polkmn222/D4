# Phase 185: Message Template UX & Logic Enhancement

## Tasks
- [x] Backup modified modules (`message_template_service.py`, `form_router.py`, `sf_form_modal.html`)
- [x] Implement real-time byte counting in `sf_form_modal.html` for MessageTemplate content.
- [x] Implement dynamic field visibility (Subject/Attachment) based on Template Type in frontend.
- [x] Implement automatic SMS -> LMS switch in frontend when content exceeds 90 bytes.
- [x] Extend the above frontend logic to "Send Message" modal (`MessageSend`).
- [x] Implement backend validation and normalization in `MessageTemplateService`:
    - Auto-switch SMS to LMS if > 90 bytes.
    - Enforce 2000 byte hard limit.
    - Clear Subject for SMS.
    - Clear Attachment for SMS/LMS.
- [x] Implement similar validation/normalization in `MessagingService.send_message`.
- [x] Update `form_router.py` to include `record_type` and `subject` in `MessageSend` new modal.
- [x] Create and run unit tests for template and send limits.
- [x] Finalize documentation (Implementation, Task, Walkthrough).
