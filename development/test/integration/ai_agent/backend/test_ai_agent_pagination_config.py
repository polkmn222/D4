import pytest
from sqlalchemy.orm import Session

from ai_agent.ui.backend.service import AiAgentService


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_pagination_default_is_30(db: Session):
    """Verify that the AI Agent service defaults to 30 records per page."""
    query = "show all leads"
    response = await AiAgentService.process_query(db, query)

    if "pagination" in response:
        assert response["pagination"]["per_page"] == 30


@pytest.mark.asyncio
async def test_execute_intent_pagination_default(db: Session):
    """Directly test _execute_intent default per_page."""
    agent_output = {"intent": "QUERY", "object_type": "lead"}
    response = await AiAgentService._execute_intent(db, agent_output, "show leads")

    if "pagination" in response:
        assert response["pagination"]["per_page"] == 30
