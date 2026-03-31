import importlib
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(ENV_PATH)


class QdrantService:
    @staticmethod
    def get_endpoint() -> str:
        endpoint = os.getenv("QDRANT_ENDPOINT", "").strip()
        if not endpoint:
            raise ValueError("QDRANT_ENDPOINT is not set.")
        return endpoint

    @staticmethod
    def get_api_key() -> str:
        api_key = os.getenv("QDRANT_API_KEY", "").strip()
        if not api_key:
            raise ValueError("QDRANT_API_KEY is not set.")
        return api_key

    @classmethod
    def _get_client_class(cls):
        module = importlib.import_module("qdrant_client")
        return module.QdrantClient

    @classmethod
    def _get_models_module(cls):
        return importlib.import_module("qdrant_client.models")

    @classmethod
    def create_client(cls):
        client_class = cls._get_client_class()
        return client_class(
            url=cls.get_endpoint(),
            api_key=cls.get_api_key(),
        )

    @classmethod
    def get_collections(cls):
        client = cls.create_client()
        return client.get_collections()

    @classmethod
    def ensure_collection(
        cls,
        collection_name: str,
        *,
        vector_size: int,
        distance: str = "COSINE",
    ) -> bool:
        client = cls.create_client()
        collections = client.get_collections()
        existing = {
            getattr(item, "name", None)
            for item in getattr(collections, "collections", [])
            if getattr(item, "name", None)
        }
        if collection_name in existing:
            return False

        models = cls._get_models_module()
        distance_value = getattr(models.Distance, str(distance).upper(), models.Distance.COSINE)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=distance_value),
        )
        return True

    @classmethod
    def build_match_filter(cls, metadata_filters: Optional[Dict[str, Any]]):
        if not metadata_filters:
            return None

        models = cls._get_models_module()
        conditions = []
        for key, value in metadata_filters.items():
            if value in (None, ""):
                continue
            conditions.append(
                models.FieldCondition(
                    key=f"metadata.{key}",
                    match=models.MatchValue(value=value),
                )
            )
        if not conditions:
            return None
        return models.Filter(must=conditions)

    @classmethod
    def upsert_points(cls, collection_name: str, points: Iterable[Dict[str, Any]]) -> Any:
        models = cls._get_models_module()
        client = cls.create_client()
        point_structs = [
            models.PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point.get("payload") or {},
            )
            for point in points
        ]
        return client.upsert(
            collection_name=collection_name,
            points=point_structs,
            wait=True,
        )

    @classmethod
    def search_points(
        cls,
        collection_name: str,
        *,
        query_vector: List[float],
        limit: int = 3,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        client = cls.create_client()
        query_filter = cls.build_match_filter(metadata_filters)

        if hasattr(client, "query_points"):
            response = client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                query_filter=query_filter,
                with_payload=True,
            )
            return list(getattr(response, "points", []) or [])

        return list(
            client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter,
                with_payload=True,
            )
        )
