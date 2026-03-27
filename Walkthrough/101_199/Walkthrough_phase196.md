## Phase 196 Walkthrough

### Summary

This phase starts the object-specific AI Agent CRUD refactor and hardens the MessageTemplate image lifecycle.

### What Changed

- Introduced a new `development/ai_agent/ui/backend/crud/` folder
- Moved lead-specific `OPEN_FORM` and `OPEN_RECORD` response building into a dedicated lead module
- Fixed MessageTemplate image lifecycle so:
  - upload is covered
  - `MMS -> SMS/LMS` clears image storage fields
  - detail data only exposes image content for `MMS`

### Verification

Focused automated verification only:

```bash
DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest \
  development/test/unit/ai_agent/backend/test_lead_crud_module.py \
  development/test/unit/ai_agent/backend/test_lead_natural_transition.py \
  development/test/unit/web/message/backend/test_message_template_image_routes.py \
  development/test/unit/web/message/frontend/templates/test_message_template_detail_visibility.py \
  development/test/unit/web/message/backend/test_message_template_modal_submission.py \
  development/test/unit/web/message/backend/test_message_template_limits.py \
  development/test/unit/messaging/test_messaging_flows.py \
  development/test/unit/web/message/backend/test_message_send_limits.py -q
```

Result:

- `31 passed, 1 warning`

### Next

- Expand the same CRUD module pattern from `lead.py` to `contact`, `opportunity`, and `message_template`
