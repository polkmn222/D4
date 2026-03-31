## Phase 337 Walkthrough

- Confirmed the list view already normalizes legacy template upload paths, but the detail route did not.
- Confirmed the detail route also had no fallback when `attachment_id` existed but `image_url` was blank.
- Fixed the detail route image resolution without expanding into unrelated upload flows.

## Verification

- Command:
  - `PYTHONPATH=development pytest -m unit development/test/unit/web/message/backend/test_message_template_image_routes.py -q`
- Result:
  - `5 passed`
