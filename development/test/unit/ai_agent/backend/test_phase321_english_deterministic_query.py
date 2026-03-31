from unittest.mock import AsyncMock, patch

import pytest

from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_search_for_lead_uses_deterministic_query_without_llm():
    expected = {
        "results": [{"id": "LEAD321A", "display_name": "Ada Kim"}],
        "sql": "SELECT * FROM leads",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "lead"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="search for lead",
            conversation_id="phase321-search-lead",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "lead"
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_edit_latest_lead_uses_recent_query_without_llm():
    expected = {
        "results": [{"id": "LEAD321B", "display_name": "Ben Park"}],
        "sql": "SELECT * FROM leads",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "lead"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="edit latest lead",
            conversation_id="phase321-edit-latest-lead",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "lead"
    assert response["data"]["query_mode"] == "recent"
    llm_call.assert_not_called()
