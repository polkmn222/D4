import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from ai_agent.llm.backend.intent_preclassifier import IntentPreClassifier
from web.backend.app.services.qdrant_service import QdrantService


class MessagePolicyRetrievalService:
    DATA_PATH = Path(__file__).resolve().parents[4] / "learning" / "message_sending_rules_qdrant.json"
    DEFAULT_COLLECTION = "message-sending-rules"
    DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
    QUESTION_HINTS = (
        "policy",
        "rule",
        "rules",
        "consent",
        "opt-out",
        "opt out",
        "blacklist",
        "dormant",
        "night",
        "marketing",
        "informational",
        "eligibility",
        "compliance",
        "동의",
        "수신거부",
        "수신 거부",
        "휴면",
        "블랙리스트",
        "야간",
        "마케팅",
        "정보성",
        "규정",
        "정책",
        "발송 가능",
        "발송 조건",
    )
    TOPIC_HINTS = (
        "message",
        "messages",
        "sms",
        "lms",
        "mms",
        "send",
        "sending",
        "recipient",
        "template",
        "메시지",
        "문자",
        "발송",
        "수신",
        "템플릿",
    )

    @classmethod
    def is_policy_question(cls, user_query: str) -> bool:
        normalized = IntentPreClassifier.normalize(user_query)
        if not any(hint in normalized for hint in cls.TOPIC_HINTS):
            return False
        if not any(hint in normalized for hint in cls.QUESTION_HINTS):
            return False
        return True

    @staticmethod
    def _contains_korean(text: str) -> bool:
        return any("\uac00" <= char <= "\ud7a3" for char in text)

    @classmethod
    def _preferred_language(cls, user_query: str, language_preference: Optional[str] = None) -> str:
        if language_preference and language_preference.lower().startswith("ko"):
            return "ko"
        if cls._contains_korean(user_query):
            return "ko"
        return "en"

    @classmethod
    def get_collection_name(cls) -> str:
        return os.getenv("QDRANT_MESSAGE_POLICY_COLLECTION", cls.DEFAULT_COLLECTION).strip() or cls.DEFAULT_COLLECTION

    @classmethod
    def get_embedding_model(cls) -> str:
        return os.getenv("OPENAI_EMBEDDING_MODEL", cls.DEFAULT_EMBEDDING_MODEL).strip() or cls.DEFAULT_EMBEDDING_MODEL

    @staticmethod
    def get_openai_api_key() -> str:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        return api_key

    @classmethod
    def load_source_documents(cls) -> List[Dict[str, Any]]:
        with cls.DATA_PATH.open("r", encoding="utf-8") as handle:
            return list(json.load(handle))

    @classmethod
    async def embed_texts(cls, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {cls.get_openai_api_key()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": cls.get_embedding_model(),
                    "input": texts,
                },
                timeout=20.0,
            )
            response.raise_for_status()
            payload = response.json()

        data = sorted(payload.get("data") or [], key=lambda item: item.get("index", 0))
        return [list(item.get("embedding") or []) for item in data]

    @classmethod
    def _build_points(cls, documents: List[Dict[str, Any]], vectors: List[List[float]]) -> List[Dict[str, Any]]:
        points = []
        for document, vector in zip(documents, vectors):
            payload = {
                "text": document["text"],
                "metadata": document.get("metadata") or {},
            }
            points.append(
                {
                    "id": document["id"],
                    "vector": vector,
                    "payload": payload,
                }
            )
        return points

    @classmethod
    async def sync_source_documents(cls) -> Dict[str, Any]:
        documents = cls.load_source_documents()
        vectors = await cls.embed_texts([document["text"] for document in documents])
        if not vectors:
            return {"count": 0, "collection_name": cls.get_collection_name()}

        QdrantService.ensure_collection(
            cls.get_collection_name(),
            vector_size=len(vectors[0]),
        )
        QdrantService.upsert_points(
            cls.get_collection_name(),
            cls._build_points(documents, vectors),
        )
        return {
            "count": len(documents),
            "collection_name": cls.get_collection_name(),
        }

    @classmethod
    async def search_policy_chunks(
        cls,
        user_query: str,
        *,
        language_preference: Optional[str] = None,
        limit: int = 3,
    ) -> List[Any]:
        vectors = await cls.embed_texts([user_query])
        if not vectors:
            return []

        return QdrantService.search_points(
            cls.get_collection_name(),
            query_vector=vectors[0],
            limit=limit,
            metadata_filters={
                "language": cls._preferred_language(user_query, language_preference),
                "topic": "message_sending",
                "status": "active",
            },
        )

    @classmethod
    def _format_hit(cls, hit: Any) -> Dict[str, Any]:
        payload = getattr(hit, "payload", None) or {}
        metadata = payload.get("metadata") or {}
        return {
            "id": getattr(hit, "id", None),
            "score": float(getattr(hit, "score", 0.0) or 0.0),
            "text": payload.get("text") or "",
            "metadata": metadata,
        }

    @classmethod
    def _build_answer_text(cls, user_query: str, hits: List[Dict[str, Any]]) -> str:
        language = cls._preferred_language(user_query)
        if language == "ko":
            intro = "메시지 발송 규정 기준으로 확인된 핵심 사항입니다:"
        else:
            intro = "These message-sending policy points are the closest match:"

        lines = [intro]
        for hit in hits:
            metadata = hit.get("metadata") or {}
            section = metadata.get("section_title") or metadata.get("title") or "Policy"
            lines.append(f"- {section}: {hit['text']}")
        return "\n".join(lines)

    @classmethod
    async def answer_policy_question(
        cls,
        user_query: str,
        *,
        language_preference: Optional[str] = None,
    ) -> Dict[str, Any]:
        hits = [cls._format_hit(hit) for hit in await cls.search_policy_chunks(user_query, language_preference=language_preference)]
        if not hits:
            language = cls._preferred_language(user_query, language_preference)
            text = (
                "메시지 발송 규정 벡터 지식베이스에서 관련 항목을 찾지 못했습니다."
                if language == "ko"
                else "I could not find a relevant item in the message-sending policy vector knowledge base."
            )
            return {"intent": "CHAT", "text": text, "score": 1.0}

        return {
            "intent": "CHAT",
            "text": cls._build_answer_text(user_query, hits),
            "score": 1.0,
            "retrieval": {
                "collection_name": cls.get_collection_name(),
                "hits": hits,
            },
        }
