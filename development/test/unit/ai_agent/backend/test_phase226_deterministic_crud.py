from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_deterministic_create_contact_returns_open_record():
    mock_contact = SimpleNamespace(
        id="CONTACT226",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="New",
    )

    with patch("web.backend.app.services.contact_service.ContactService.create_contact", return_value=mock_contact):
        response = await AiAgentService.process_query(
            db=None,
            user_query="create contact first name Ada last name Kim status New email ada@example.com phone 010-1234-5678",
            conversation_id="phase226-contact-create",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "contact"
    assert response["record_id"] == "CONTACT226"
    assert response["redirect_url"] == "/contacts/CONTACT226"


@pytest.mark.asyncio
async def test_deterministic_create_opportunity_returns_open_record():
    mock_opportunity = SimpleNamespace(
        id="OPP226",
        name="Q2 Deal",
        stage="Qualification",
        amount=50000,
        probability=10,
        status="Open",
    )

    with patch("web.backend.app.services.opportunity_service.OpportunityService.create_opportunity", return_value=mock_opportunity):
        response = await AiAgentService.process_query(
            db=None,
            user_query="create opportunity name Q2 Deal stage Qualification amount 50000",
            conversation_id="phase226-opp-create",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "opportunity"
    assert response["record_id"] == "OPP226"
    assert response["redirect_url"] == "/opportunities/OPP226"


@pytest.mark.asyncio
async def test_deterministic_update_contact_returns_refreshed_open_record():
    mock_contact = SimpleNamespace(
        id="CONTACT226U",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01099998888",
        status="Qualified",
    )

    with patch("web.backend.app.services.contact_service.ContactService.update_contact", return_value=mock_contact), patch(
        "web.backend.app.services.contact_service.ContactService.get_contact", return_value=mock_contact
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="update contact CONTACT226U phone 01099998888 status Qualified",
            conversation_id="phase226-contact-update",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "contact"
    assert response["record_id"] == "CONTACT226U"
    assert response["redirect_url"] == "/contacts/CONTACT226U"


@pytest.mark.asyncio
async def test_deterministic_update_opportunity_returns_refreshed_open_record():
    mock_opportunity = SimpleNamespace(
        id="OPP226U",
        name="Q2 Deal",
        stage="Closed Won",
        amount=50000,
        probability=90,
        status="Open",
    )

    with patch("web.backend.app.services.opportunity_service.OpportunityService.update_opportunity", return_value=mock_opportunity), patch(
        "web.backend.app.services.opportunity_service.OpportunityService.get_opportunity", return_value=mock_opportunity
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="update opportunity OPP226U stage Closed Won probability 90",
            conversation_id="phase226-opp-update",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "opportunity"
    assert response["record_id"] == "OPP226U"
    assert response["redirect_url"] == "/opportunities/OPP226U"


@pytest.mark.asyncio
async def test_all_contacts_returns_query_without_llm():
    expected = {
        "results": [{"id": "CONTACT1", "display_name": "Ada Kim"}],
        "sql": "SELECT * FROM contacts",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "contact"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble"
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="all contacts",
            conversation_id="phase226-all-contacts",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "contact"
    assert response["results"] == expected["results"]
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_recent_opportunities_returns_query_without_llm():
    expected = {
        "results": [{"id": "OPP1", "name": "Recent Deal"}],
        "sql": "SELECT * FROM opportunities",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "opportunity"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble"
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="recent opportunities",
            conversation_id="phase226-recent-opps",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "opportunity"
    assert response["results"] == expected["results"]
    llm_call.assert_not_called()


@pytest.mark.asyncio
async def test_ambiguous_update_contact_returns_safe_chat_response():
    with patch.object(AiAgentService, "_call_multi_llm_ensemble") as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="update contact",
            conversation_id="phase226-ambiguous-contact",
        )

    assert response["intent"] == "CHAT"
    assert "record ID" in response["text"]
    llm_call.assert_not_called()
