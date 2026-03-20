# Implementation Plan - Phase 39: Messaging Mobile Preview Refinement

This phase focuses on refining the Mobile Preview UI in the Send Message screen to improve visual hierarchy and handle image-only messages elegantly.

## Proposed Changes

### 1. Messaging UI (Templates)

#### [MODIFY] [send_message.html](file:///Users/sangyeol.park@gruve.ai/Documents/D4/app/templates/messages/send_message.html)
- Set `flex-direction: column` on `#preview-msg-container` to ensure vertical stacking (image top, text bottom).
- Adjust initial styles to support dynamic layout.

### 2. Messaging UI (JavaScript)

#### [MODIFY] [messaging.js](file:///Users/sangyeol.park@gruve.ai/Documents/D4/app/static/js/messaging.js)
- Modify `UIManager.updatePreview` to:
    - Hide the `#preview-bubble` if the message content is empty but an image is attached.
    - Dynamically adjust the `border-radius` of the preview image:
        - If text exists below: `15px 15px 4px 4px` (rounded top).
        - If no text exists: `15px` (fully rounded).
- Ensure the container correctly shows/hides based on both content and image presence.

## Verification Plan

### Automated Tests
- N/A (UI visual changes)

### Manual Verification
1.  **Open Send Message screen**.
2.  **Scenario: Text Only**
    - Verify text appears in a bubble in the mobile preview.
3.  **Scenario: Image + Text**
    - Upload an image.
    - Verify image is at the top, text is directly below.
    - Verify image top corners are rounded (15px) and bottom corners are subtly rounded (4px) to blend with the bubble.
4.  **Scenario: Image Only**
    - Remove text.
    - Verify "Photo Attachment" text is NOT visible.
    - Verify image is fully rounded (15px).
    - Verify preview bubble is hidden.
