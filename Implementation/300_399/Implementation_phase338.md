## Phase 338 Implementation

- Updated `development/web/frontend/templates/templates/sf_form_modal.html`:
  - added hidden `remove_image` field
  - changed modal image actions to scoped picker helpers
  - changed `Clear Selection` to `Clear Image`
  - added staged helper text for selected/remove states
  - aligned validation with detail-tab staged image behavior
- Updated `development/web/message/backend/routers/message_template_router.py`:
  - accepted `remove_image` in template update route
  - applied staged removal before save completion, even for AI Agent fallback form posts
- Updated `development/ai_agent/ui/frontend/static/js/ai_agent.js`:
  - AI-managed inline submit now falls back to normal form submit when template image removal is staged
  - scoped AI modal renderer respects the shared modal remove-image state
- Added/updated unit coverage in:
  - `development/test/unit/web/message/backend/test_message_template_image_routes.py`
  - `development/test/unit/web/frontend/test_ui_js_logic.py`
  - `development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py`
