# Phase 203 Lead Explicit-ID Manual Check

## Environment

- Runtime: local `uvicorn api.index:app`
- Database: configured PostgreSQL from `development/.env`
- Date: 2026-03-26

## Automated Validation

- Command:
  - `PYTHONPATH=development pytest development/test/unit/ai_agent/backend/test_lead_crud_logic_phase177.py development/test/unit/ai_agent/backend/test_lead_crud_module.py development/test/unit/ai_agent/backend/test_ai_agent_lead_real_db_phase177_v2.py -q`
- Result:
  - `18 passed, 1 warning`

## Manual HTTP Validation

### Setup

1. Create lead via web
- Request:
  - `POST /leads/`
- Result:
  - `303 See Other`
  - Redirect: `/leads/00Q5sxcoZvaPfGEEI0?success=Record+created+successfully`

### AI Agent explicit-ID CRUD

1. Show by ID
- Request:
  - `POST /ai-agent/api/chat`
  - Query: `show lead 00Q5sxcoZvaPfGEEI0`
- Result:
  - `OPEN_RECORD`
  - Redirect URL: `/leads/00Q5sxcoZvaPfGEEI0`
  - Text used the lead name, not the raw ID

2. Edit by ID
- Request:
  - `POST /ai-agent/api/chat`
  - Query: `edit lead 00Q5sxcoZvaPfGEEI0`
- Result:
  - `OPEN_FORM`
  - Form URL: `/leads/new-modal?id=00Q5sxcoZvaPfGEEI0`
  - Form title used the lead name

3. Update by ID
- Request:
  - `POST /ai-agent/api/chat`
  - Query: `update lead 00Q5sxcoZvaPfGEEI0 status Lost`
- Result:
  - `OPEN_RECORD`
  - Updated chat card subtitle: `Lead · Lost`

4. Delete by ID
- Request:
  - `POST /ai-agent/api/chat`
  - Query: `delete lead 00Q5sxcoZvaPfGEEI0`
- Result:
  - `DELETE`
  - Text: `Success! Deleted lead Phase203 Phase203Web1774500095 (01020300095).`

5. Deleted record verification
- Request:
  - `GET /leads/00Q5sxcoZvaPfGEEI0`
- Result:
  - `307 Temporary Redirect`
  - Redirect: `/leads?error=Lead+not+found`

## Conclusion

- AI Agent explicit-ID lead CRUD now works for show, edit, update, and delete.
- User-facing text and workspace labels no longer need to fall back to raw record IDs.
