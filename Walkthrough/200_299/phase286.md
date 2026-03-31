Phase 286 Verification

- Confirmed the template exposes `window.__messagingRecipientApi`.
- Confirmed the shared messaging module delegates to the template owner for select-all and filtering.

Tests:
- `PYTHONPATH=development pytest -m unit development/test/unit/web/frontend/test_phase276_loading_and_list_view_contract.py -q`
