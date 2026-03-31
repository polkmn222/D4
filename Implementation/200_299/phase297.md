# Phase 297 Implementation

## Scope
- Remove recommendation count drift between home, Send Message, and AI Agent.

## Changes
- Reworked `AIRecommendationService.get_sendable_recommendations(...)` to support unlimited shared datasets.
- Removed per-surface recommendation limits from:
  - dashboard recommendation router
  - messaging recommendation router
  - AI Agent `RECOMMEND` execution path
- Updated tests to assert that all three surfaces consume the same shared source without per-surface limits.

## Files
- `development/ai_agent/llm/backend/recommendations.py`
- `development/web/backend/app/api/routers/dashboard_router.py`
- `development/web/message/backend/router.py`
- `development/ai_agent/ui/backend/service.py`
- `development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py`
- `development/test/unit/ai_agent/frontend/test_phase278_query_and_recommend_contract.py`
