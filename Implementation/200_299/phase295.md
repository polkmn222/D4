# Phase 295 Implementation

## Scope
- Restore AI Agent create/edit continuity for grouped objects after inline web form submit.
- Align opportunity/contact form contracts with current requirements.
- Unify open/edit/new behavior closer to web form structure.
- Prevent top-scroll jumps after inline form save.

## Changes
- Updated AI Agent opportunity form contract:
  - required fields are now `contact`, `name`, `stage`
  - `status` is hidden from AI Agent and web modal forms
- Updated AI Agent contact form contract:
  - `status` is hidden
  - create/edit default status is preserved internally as `New`
- Preserved hidden/default opportunity status internally as `Open`
- Reused existing record values during edit validation so save-without-change does not fail on required hidden fields
- Expanded opportunity open record card to include lookup-linked fields:
  - Contact, Brand, Model, Product, Asset, Probability
- Restored inline web form submit continuity:
  - resolve redirected detail URL back into AI Agent `OPEN_RECORD`
  - stop falling back to generic `Record saved successfully`
  - stop reopening workspace after successful inline submit
- Fixed grouped object edit route mapping:
  - `brand` edit uses `type=Brand`
  - `message_template` edit route enabled
- Added edit/delete actions to message template open card
- Set AI Agent window zoom to `90%`

## Files
- `development/ai_agent/ui/backend/service.py`
- `development/ai_agent/ui/frontend/static/js/ai_agent.js`
- `development/ai_agent/ui/frontend/static/css/ai_agent.css`
- `development/web/backend/app/api/form_router.py`
- `development/web/backend/app/api/routers/opportunity_router.py`
- `development/web/backend/app/services/opportunity_service.py`
- related unit/DOM test files
