# Phase 200 Implementation Plan

## Planned Changes

1. Remove create-time leakage of `_force_null_fields` into the `Lead` SQLAlchemy constructor.
2. Add focused unit coverage for lead creation when empty lookup fields are present.
3. Re-run targeted unit tests.
4. Run PostgreSQL-backed manual validation for:
   - direct web lead create
   - direct web lead edit
   - AI Agent lead create through `/ai-agent/api/chat`

## Verification

- `PYTHONPATH=development DATABASE_URL=sqlite:///:memory: pytest development/test/unit/ai_agent/backend/test_lead_crud_logic_phase177.py development/test/unit/ai_agent/backend/test_lead_crud_module.py development/test/unit/web/message/backend/test_message_template_modal_submission.py -q`
