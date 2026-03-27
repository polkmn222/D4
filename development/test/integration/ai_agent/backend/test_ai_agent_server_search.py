import pytest
from sqlalchemy.orm import Session

from ai_agent.ui.backend.service import AiAgentService


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_server_side_search_sql_generation(db: Session):
    """Verify that a search query generates SQL with ILIKE clauses."""
    query = "search leads for John"
    response = await AiAgentService.process_query(db, query)

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "lead"
    assert "sql" in response
    sql = response["sql"].lower()
    assert "ilike" in sql
    assert "%john%" in sql
    assert "first_name" in sql or "last_name" in sql or "email" in sql


@pytest.mark.asyncio
async def test_search_no_results_pagination(db: Session):
    """Verify that search returns a valid pagination object even with no results."""
    query = "search leads for NonExistentRecord123456"
    response = await AiAgentService.process_query(db, query)

    assert response["intent"] == "QUERY"
    assert "pagination" in response
    assert response["pagination"]["total"] == 0
    assert response["results"] == []
