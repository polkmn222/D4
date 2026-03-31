## Phase 337 Implementation

- Added `_resolve_template_image_url()` in `development/web/message/backend/routers/message_template_router.py`.
- The detail route now:
  - normalizes legacy `/static/uploads/templates/` paths to `/static/uploads/message_templates/`
  - falls back to the linked attachment file path when `image_url` is blank
- Added unit coverage in `development/test/unit/web/message/backend/test_message_template_image_routes.py`.
