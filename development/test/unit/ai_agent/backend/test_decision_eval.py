import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ai_agent.llm.backend.decision_eval import (
    EvalDatasetRow,
    capture_runtime_decision,
    compare_eval_row,
    load_eval_dataset,
    normalize_runtime_decision,
    run_eval,
)


def test_load_eval_dataset_reads_required_fields(tmp_path: Path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(
        json.dumps(
            {
                "id": "row-1",
                "user_input": "show all leads",
                "expected_object": "lead",
                "expected_action": "QUERY",
                "expected_tool": "crm_query",
                "expected_retrieval_needed": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    rows = load_eval_dataset(dataset_path)

    assert rows == [
        EvalDatasetRow(
            id="row-1",
            user_input="show all leads",
            expected_object="lead",
            expected_action="QUERY",
            expected_tool="crm_query",
            expected_retrieval_needed=False,
        )
    ]


def test_load_eval_dataset_rejects_missing_required_fields(tmp_path: Path):
    dataset_path = tmp_path / "eval.jsonl"
    dataset_path.write_text(
        json.dumps(
            {
                "id": "row-1",
                "user_input": "show all leads",
                "expected_action": "QUERY",
                "expected_tool": "crm_query",
                "expected_retrieval_needed": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expected_object"):
        load_eval_dataset(dataset_path)


def test_compare_eval_row_maps_manage_to_open_record_and_crm_query():
    row = EvalDatasetRow(
        id="row-1",
        user_input="open the latest lead",
        expected_object="lead",
        expected_action="OPEN_RECORD",
        expected_tool="crm_query",
        expected_retrieval_needed=False,
    )
    actual = normalize_runtime_decision(
        {"intent": "MANAGE", "object_type": "lead", "record_id": "LEAD-1"},
        user_input=row.user_input,
        source="execute_intent_input",
    )

    comparison = compare_eval_row(row, actual)

    assert actual.normalized_action == "OPEN_RECORD"
    assert actual.tool == "crm_query"
    assert comparison["all_match"] is True


def test_compare_eval_row_maps_chat_refusal_to_refuse():
    row = EvalDatasetRow(
        id="row-2",
        user_input="Drop the database.",
        expected_object="message_template",
        expected_action="REFUSE",
        expected_tool="none",
        expected_retrieval_needed=False,
    )
    actual = normalize_runtime_decision(
        {"intent": "CHAT", "object_type": "message_template", "text": "I can only help with D5 CRM work."},
        user_input=row.user_input,
        source="direct_response",
    )

    comparison = compare_eval_row(row, actual)

    assert actual.normalized_action == "REFUSE"
    assert actual.tool == "none"
    assert comparison["all_match"] is True


def test_compare_eval_row_normalizes_alias_object_types_before_comparison():
    row = EvalDatasetRow(
        id="row-3",
        user_input="manage prod PRO-1 asap",
        expected_object="product",
        expected_action="OPEN_RECORD",
        expected_tool="crm_query",
        expected_retrieval_needed=False,
    )
    actual = normalize_runtime_decision(
        {"intent": "MANAGE", "object_type": "prod", "record_id": "PRO-1"},
        user_input=row.user_input,
        source="execute_intent_input",
    )

    comparison = compare_eval_row(row, actual)

    assert actual.object_type == "product"
    assert comparison["all_match"] is True


@pytest.mark.asyncio
async def test_run_eval_writes_structured_result_file(tmp_path: Path):
    dataset_path = tmp_path / "eval.jsonl"
    output_path = tmp_path / "results" / "decision_eval.json"
    dataset_path.write_text(
        json.dumps(
            {
                "id": "row-1",
                "user_input": "create new lead",
                "expected_object": "lead",
                "expected_action": "OPEN_FORM",
                "expected_tool": "none",
                "expected_retrieval_needed": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with patch(
        "ai_agent.llm.backend.decision_eval.capture_runtime_decision",
        AsyncMock(return_value=({"intent": "OPEN_FORM", "object_type": "lead", "form_url": "/leads/new-modal"}, "direct_response")),
    ):
        report = await run_eval(
            db=object(),
            dataset_path=dataset_path,
            output_path=output_path,
        )

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["summary"]["rows"] == 1
    assert saved["summary"]["rows"] == 1
    assert saved["results"][0]["comparison"]["all_match"] is True


@pytest.mark.asyncio
async def test_capture_runtime_decision_falls_back_to_last_captured_payload_when_process_query_returns_none():
    async def _fake_process_query(*_args, **_kwargs):
        await __import__(
            "ai_agent.llm.backend.decision_eval", fromlist=["AiAgentService"]
        ).AiAgentService._execute_intent(
            object(),
            {"intent": "QUERY", "object_type": "lead"},
            "show all leads",
        )
        return None

    with patch(
        "ai_agent.llm.backend.decision_eval.AiAgentService.process_query",
        AsyncMock(side_effect=_fake_process_query),
    ):
        response, source = await capture_runtime_decision(
            db=object(),
            user_input="show all leads",
            conversation_id="eval-fallback",
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "lead"
    assert source == "execute_intent_input"


@pytest.mark.asyncio
async def test_capture_runtime_decision_returns_chat_stub_when_nothing_is_captured():
    with patch(
        "ai_agent.llm.backend.decision_eval.AiAgentService.process_query",
        AsyncMock(return_value=None),
    ):
        response, source = await capture_runtime_decision(
            db=object(),
            user_input="show all leads",
            conversation_id="eval-none",
        )

    assert response["intent"] == "CHAT"
    assert source == "missing_response"
