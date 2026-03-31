## Phase 338 Walkthrough

- Confirmed the detail tab already supported staged image replace/remove for templates.
- Confirmed the shared modal did not have a remove-image state and only cleared local preview data.
- Confirmed AI Agent modal reused the shared modal, but AI-managed submit needed to fall back to the regular form post when image removal was staged.
- Applied the smallest shared fix path so web edit modal and AI Agent modal now follow the detail-tab image workflow.

## Verification

- Command:
  - `PYTHONPATH=development pytest -m unit development/test/unit/web/message/backend/test_message_template_image_routes.py development/test/unit/web/frontend/test_ui_js_logic.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py -q`
- Result:
  - `71 passed`
