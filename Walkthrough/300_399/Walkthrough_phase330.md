# Phase 330 Walkthrough

## What Changed

The web `MessageTemplate` detail page already staged image upload/removal until the shared Save action, but the inline edit UI only showed `Replace Image` and `Clear Image` buttons. Because the standard detail inline edit flow hides the display node while editing, users could not see the selected image preview in edit mode.

Phase 330 adds an edit-state image panel with:

- an empty state for templates without an image
- a preview state for existing and newly selected images
- replace and clear actions within the preview panel
- helper text that continues to show staged-save guidance

The existing `renderTemplateDetailImageCard(...)` helper now keeps the display card and edit-state panel in sync.

## Verification

- `PYTHONPATH=development pytest -m unit development/test/unit/web/message/backend/test_message_template_modal_submission.py -q`
- Result: `18 passed`

## Not Run

- Manual browser verification was not run by policy.
