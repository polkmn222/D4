# Phase 202 Walkthrough

## Summary

- Ran a PostgreSQL-backed validation pass focused on Lead CRUD only.
- Web lead CRUD passed create, read/open, update, and delete in live HTTP checks.
- AI Agent lead CRUD still has runtime defects and is not fully aligned with the web lead CRUD contract.

## Validation

- Focused PostgreSQL-backed unit tests:
  - `PYTHONPATH=development pytest development/test/unit/crm/test_core_crud.py::test_lead_crud development/test/unit/crm/test_related_lookup_sync.py::test_lead_product_lookup_sync development/test/unit/ai_agent/backend/test_lead_flow_consistency.py development/test/unit/ai_agent/backend/test_lead_natural_transition.py development/test/unit/ai_agent/backend/test_lead_crud_logic_phase171.py development/test/unit/ai_agent/backend/test_lead_crud_logic_phase177.py development/test/unit/ai_agent/backend/test_ai_agent_lead_real_db_phase177_v2.py -q`
  - Result: `24 passed`
- Manual evidence:
  - [http_manual_check.md](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/manual/evidence/phase202/http_manual_check.md)

## Findings

- AI Agent `create lead ...` failed in live PostgreSQL validation with:
  - `company_name is an invalid keyword argument for Lead`
- AI Agent `show lead {id}` returned a generic list `QUERY` response instead of opening the requested lead.
- AI Agent `update lead {id} ...`, `edit lead {id}`, and `delete lead {id}` returned guidance text instead of executing the explicit-id CRUD flow.
