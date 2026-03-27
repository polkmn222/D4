# Phase 202 Lead CRUD Manual Check

## Environment

- Runtime: local `uvicorn api.index:app`
- Database: configured PostgreSQL from `development/.env`
- Date: 2026-03-26

## Automated Validation

- Command:
  - `PYTHONPATH=development pytest development/test/unit/crm/test_core_crud.py::test_lead_crud development/test/unit/crm/test_related_lookup_sync.py::test_lead_product_lookup_sync development/test/unit/ai_agent/backend/test_lead_flow_consistency.py development/test/unit/ai_agent/backend/test_lead_natural_transition.py development/test/unit/ai_agent/backend/test_lead_crud_logic_phase171.py development/test/unit/ai_agent/backend/test_lead_crud_logic_phase177.py development/test/unit/ai_agent/backend/test_ai_agent_lead_real_db_phase177_v2.py -q`
- Result:
  - `24 passed in 15.65s`

## Manual HTTP Validation

### Web Lead CRUD

1. Create
- Request:
  - `POST /leads/`
- Result:
  - `303 See Other`
  - Redirect: `/leads/00QkSk0YVVsGq0hU2C?success=Record+created+successfully`

2. Read / Open
- Request:
  - `GET /leads/00QkSk0YVVsGq0hU2C?success=Record+created+successfully`
- Result:
  - `200 OK`
  - Detail page rendered with title `Phase202 Phase202Web1774499012 | Lead - Salesforce`

3. Update
- Request:
  - `POST /leads/00QkSk0YVVsGq0hU2C/update`
- Payload summary:
  - `last_name=Phase202WebUpdated`
  - `email=phase202_web_updated@example.com`
  - `phone=01020209999`
  - `status=Qualified`
- Result:
  - `303 See Other`
  - Redirect: `/leads/00QkSk0YVVsGq0hU2C?success=Record+updated+successfully`

4. Delete
- Request:
  - `POST /leads/00QkSk0YVVsGq0hU2C/delete`
- Headers:
  - `Accept: application/json`
- Result:
  - `200 OK`
  - Body: `{"status":"success","message":"Record deleted successfully"}`

5. PostgreSQL verification
- Before delete/update check:
  - lead `00QkSk0YVVsGq0hU2C` existed and reflected updated values
- After delete:
  - `deleted_at` was populated for `00QkSk0YVVsGq0hU2C`

### AI Agent Lead CRUD

1. Create
- Request:
  - `POST /ai-agent/api/chat`
  - Query shape: `create lead first name Phase202AI ...`
- Result:
  - Failed
  - Response: `{"intent":"CHAT","text":"Technical issue: 'company_name' is an invalid keyword argument for Lead"}`
- Status:
  - Defect confirmed

2. Read by ID
- Request:
  - `POST /ai-agent/api/chat`
  - Query: `show lead 00Qh3xlS7PXsXNlEUN`
- Result:
  - Returned `QUERY`
  - Returned paginated lead list instead of an open/manage response for the requested record id
- Status:
  - Defect confirmed

3. Update by ID
- Request:
  - `POST /ai-agent/api/chat`
  - Query: `update lead 00Qh3xlS7PXsXNlEUN status Lost`
- Result:
  - Returned guidance text instead of updating the record
  - Response asked user to first show/select the record
- Status:
  - Defect confirmed

4. Edit by ID
- Request:
  - `POST /ai-agent/api/chat`
  - Query: `edit lead 00Qh3xlS7PXsXNlEUN`
- Result:
  - Returned guidance text instead of `OPEN_FORM`
- Status:
  - Defect confirmed

5. Delete by ID
- Request:
  - `POST /ai-agent/api/chat`
  - Query: `delete lead 00Qh3xlS7PXsXNlEUN`
- Result:
  - Returned guidance text instead of entering delete flow for the explicit id
- Status:
  - Defect confirmed

6. PostgreSQL verification for AI Agent target record
- Record checked:
  - `00Qh3xlS7PXsXNlEUN`
- Result:
  - Still present
  - `status='Qualified'`
  - `deleted_at IS NULL`

## Conclusion

- Web lead CRUD passed create, read/open, update, and delete.
- AI Agent lead CRUD is not fully aligned with the web lead contract.
- Confirmed runtime issues:
  - create path leaks `company_name`
  - read-by-id does not open the requested record
  - update/edit/delete by explicit id do not execute the expected lead CRUD flow
