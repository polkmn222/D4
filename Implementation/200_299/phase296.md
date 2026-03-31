# Phase 296 Implementation

## Scope
- Align AI Agent `AI Recommend` and `Change AI Recommend` behavior with the home tab recommendation contract.

## Changes
- Added `DASHBOARD_RECOMMENDATION_LIMIT = 4` to the shared recommendation service.
- Updated dashboard recommendation router to use the shared dashboard limit constant.
- Updated AI Agent `RECOMMEND` execution path to use `get_sendable_recommendations(...)` instead of the broader raw recommendation list.
- Updated tests to lock the shared source/limit contract.

## Files
- `development/ai_agent/llm/backend/recommendations.py`
- `development/ai_agent/ui/backend/service.py`
- `development/web/backend/app/api/routers/dashboard_router.py`
- `development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py`
- `development/test/unit/ai_agent/frontend/test_phase278_query_and_recommend_contract.py`
