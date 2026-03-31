import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from ai_agent.llm.backend.message_policy_retrieval import MessagePolicyRetrievalService
from ai_agent.ui.backend.service import AiAgentService


def test_is_policy_question_detects_message_policy_queries():
    assert MessagePolicyRetrievalService.is_policy_question("What is the opt-out policy for marketing messages?")
    assert MessagePolicyRetrievalService.is_policy_question("야간 마케팅 메시지 발송 규정 알려줘")
    assert not MessagePolicyRetrievalService.is_policy_question("show recent contacts")


@pytest.mark.asyncio
async def test_sync_source_documents_embeds_and_upserts(monkeypatch, tmp_path):
    source_path = tmp_path / "message_rules.json"
    source_path.write_text(
        json.dumps(
            [
                {
                    "id": "msg_rules_ko_001",
                    "text": "야간 발송은 제한됩니다.",
                    "metadata": {"language": "ko", "topic": "message_sending", "status": "active"},
                },
                {
                    "id": "msg_rules_en_001",
                    "text": "Marketing messages require consent.",
                    "metadata": {"language": "en", "topic": "message_sending", "status": "active"},
                },
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(MessagePolicyRetrievalService, "DATA_PATH", Path(source_path))
    monkeypatch.setattr(
        MessagePolicyRetrievalService,
        "embed_texts",
        AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]]),
    )

    with patch(
        "ai_agent.llm.backend.message_policy_retrieval.QdrantService.ensure_collection"
    ) as ensure_collection, patch(
        "ai_agent.llm.backend.message_policy_retrieval.QdrantService.upsert_points"
    ) as upsert_points:
        result = await MessagePolicyRetrievalService.sync_source_documents()

    assert result["count"] == 2
    ensure_collection.assert_called_once()
    upsert_points.assert_called_once()
    collection_name, points = upsert_points.call_args.args
    assert collection_name == MessagePolicyRetrievalService.get_collection_name()
    assert [point["id"] for point in points] == ["msg_rules_ko_001", "msg_rules_en_001"]


@pytest.mark.asyncio
async def test_answer_policy_question_formats_retrieved_hits(monkeypatch):
    monkeypatch.setattr(
        MessagePolicyRetrievalService,
        "search_policy_chunks",
        AsyncMock(
            return_value=[
                SimpleNamespace(
                    id="msg_rules_ko_006",
                    score=0.93,
                    payload={
                        "text": "오후 8시부터 다음 날 오전 8시 사이의 야간 마케팅 발송은 제한됩니다.",
                        "metadata": {
                            "section_title": "6. 야간 발송 제한 및 예약 발송",
                            "language": "ko",
                        },
                    },
                )
            ]
        ),
    )

    response = await MessagePolicyRetrievalService.answer_policy_question("야간 마케팅 문자 발송 규정 알려줘")

    assert response["intent"] == "CHAT"
    assert "야간 발송 제한" in response["text"]
    assert response["retrieval"]["hits"][0]["id"] == "msg_rules_ko_006"


@pytest.mark.asyncio
async def test_ai_agent_process_query_uses_message_policy_retrieval():
    fake_response = {
        "intent": "CHAT",
        "text": "These message-sending policy points are the closest match:\n- 2. Principle of Consent Verification: Marketing messages require consent.",
        "score": 1.0,
    }

    with patch(
        "ai_agent.ui.backend.service.MessagePolicyRetrievalService.is_policy_question",
        return_value=True,
    ), patch(
        "ai_agent.ui.backend.service.MessagePolicyRetrievalService.answer_policy_question",
        AsyncMock(return_value=fake_response),
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="What is the consent rule for marketing messages?",
            conversation_id="phase319-policy",
        )

    assert response == fake_response


@pytest.mark.asyncio
async def test_ai_agent_process_query_reports_missing_vector_configuration():
    with patch(
        "ai_agent.ui.backend.service.MessagePolicyRetrievalService.is_policy_question",
        return_value=True,
    ), patch(
        "ai_agent.ui.backend.service.MessagePolicyRetrievalService.answer_policy_question",
        AsyncMock(side_effect=ValueError("OPENAI_API_KEY is not set.")),
    ):
        response = await AiAgentService.process_query(
            db=None,
            user_query="야간 마케팅 메시지 규정 알려줘",
            conversation_id="phase319-policy-config",
        )

    assert response["intent"] == "CHAT"
    assert "벡터 검색" in response["text"]
