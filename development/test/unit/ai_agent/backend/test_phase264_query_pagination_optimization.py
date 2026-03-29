from types import SimpleNamespace
from unittest.mock import MagicMock

from ai_agent.ui.backend.service import AiAgentService


def _row(mapping):
    return SimpleNamespace(_mapping=mapping)


def test_first_page_small_result_set_skips_count_query():
    db = MagicMock()
    preview_rows = [_row({"id": "LEAD1", "display_name": "Ada Kim"})]
    db.execute.side_effect = [preview_rows]

    result = AiAgentService._execute_paginated_query(
        db,
        "SELECT id, display_name FROM leads",
        "lead",
        page=1,
        per_page=30,
    )

    assert result["results"] == [{"id": "LEAD1", "display_name": "Ada Kim"}]
    assert result["pagination"]["total"] == 1
    assert result["pagination"]["total_pages"] == 1
    assert db.execute.call_count == 1


def test_first_page_overflow_still_runs_count_query_for_exact_pagination():
    db = MagicMock()
    preview_rows = [_row({"id": f"LEAD{i}", "display_name": f"Lead {i}"}) for i in range(31)]
    count_result = MagicMock()
    count_result.scalar.return_value = 31
    db.execute.side_effect = [preview_rows, count_result]

    result = AiAgentService._execute_paginated_query(
        db,
        "SELECT id, display_name FROM leads",
        "lead",
        page=1,
        per_page=30,
    )

    assert len(result["results"]) == 30
    assert result["pagination"]["total"] == 31
    assert result["pagination"]["total_pages"] == 2
    assert db.execute.call_count == 2
