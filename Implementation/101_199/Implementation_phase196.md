## Phase 196 Implementation

### New AI Agent CRUD Module Layout

- Added [crud/__init__.py](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/backend/crud/__init__.py)
- Added [lead.py](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/backend/crud/lead.py)

The new lead module now owns the lead-specific UI contracts for:

- `OPEN_FORM` edit response
- `OPEN_RECORD` response after lead create/update/manage

The main AI Agent service now delegates those lead-specific contracts to the new module instead of building them inline.

### MessageTemplate Image Flow

- Added `_clear_template_image_fields()` in [message_template_router.py](/Users/sangyeol.park@gruve.ai/Documents/D5/development/web/message/backend/routers/message_template_router.py)
- MessageTemplate detail now only exposes `Image` data when `record_type == "MMS"`
- Switching a template away from `MMS` now removes the stored template image and clears the image fields
- `clear-image` now reuses the same field-reset helper

### Test Coverage

- Added [test_lead_crud_module.py](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/backend/test_lead_crud_module.py)
- Added [test_message_template_image_routes.py](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/web/message/backend/test_message_template_image_routes.py)
- Kept lead natural transition tests and template visibility tests in the focused suite
