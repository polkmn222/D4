from types import SimpleNamespace

import pytest

from web.backend.app.services.qdrant_service import QdrantService


def test_get_endpoint_returns_trimmed_env_value(monkeypatch):
    monkeypatch.setenv("QDRANT_ENDPOINT", " https://example.qdrant.io ")

    assert QdrantService.get_endpoint() == "https://example.qdrant.io"


def test_get_endpoint_raises_when_env_is_missing(monkeypatch):
    monkeypatch.delenv("QDRANT_ENDPOINT", raising=False)

    with pytest.raises(ValueError, match="QDRANT_ENDPOINT is not set."):
        QdrantService.get_endpoint()


def test_get_api_key_returns_trimmed_env_value(monkeypatch):
    monkeypatch.setenv("QDRANT_API_KEY", " secret-key ")

    assert QdrantService.get_api_key() == "secret-key"


def test_get_api_key_raises_when_env_is_missing(monkeypatch):
    monkeypatch.delenv("QDRANT_API_KEY", raising=False)

    with pytest.raises(ValueError, match="QDRANT_API_KEY is not set."):
        QdrantService.get_api_key()


def test_create_client_uses_endpoint_and_api_key(monkeypatch):
    captured = {}

    class FakeQdrantClient:
        def __init__(self, *, url, api_key):
            captured["url"] = url
            captured["api_key"] = api_key

    monkeypatch.setenv("QDRANT_ENDPOINT", "https://example.qdrant.io")
    monkeypatch.setenv("QDRANT_API_KEY", "secret-key")
    monkeypatch.setattr(
        QdrantService,
        "_get_client_class",
        classmethod(lambda cls: FakeQdrantClient),
    )

    client = QdrantService.create_client()

    assert isinstance(client, FakeQdrantClient)
    assert captured == {
        "url": "https://example.qdrant.io",
        "api_key": "secret-key",
    }


def test_get_collections_delegates_to_client(monkeypatch):
    expected = SimpleNamespace(collections=[{"name": "crm-knowledge"}])

    class FakeQdrantClient:
        def get_collections(self):
            return expected

    monkeypatch.setattr(
        QdrantService,
        "create_client",
        classmethod(lambda cls: FakeQdrantClient()),
    )

    assert QdrantService.get_collections() is expected


def test_ensure_collection_creates_missing_collection(monkeypatch):
    captured = {}

    class FakeVectorParams:
        def __init__(self, *, size, distance):
            self.size = size
            self.distance = distance

    fake_models = SimpleNamespace(
        Distance=SimpleNamespace(COSINE="cosine"),
        VectorParams=FakeVectorParams,
    )

    class FakeClient:
        def get_collections(self):
            return SimpleNamespace(collections=[SimpleNamespace(name="existing")])

        def create_collection(self, *, collection_name, vectors_config):
            captured["collection_name"] = collection_name
            captured["vector_size"] = vectors_config.size
            captured["distance"] = vectors_config.distance

    monkeypatch.setattr(QdrantService, "create_client", classmethod(lambda cls: FakeClient()))
    monkeypatch.setattr(QdrantService, "_get_models_module", classmethod(lambda cls: fake_models))

    created = QdrantService.ensure_collection("message-sending-rules", vector_size=1536)

    assert created is True
    assert captured == {
        "collection_name": "message-sending-rules",
        "vector_size": 1536,
        "distance": "cosine",
    }


def test_ensure_collection_skips_existing_collection(monkeypatch):
    class FakeClient:
        def get_collections(self):
            return SimpleNamespace(collections=[SimpleNamespace(name="message-sending-rules")])

        def create_collection(self, **_kwargs):
            raise AssertionError("create_collection should not be called")

    monkeypatch.setattr(QdrantService, "create_client", classmethod(lambda cls: FakeClient()))

    created = QdrantService.ensure_collection("message-sending-rules", vector_size=1536)

    assert created is False


def test_upsert_points_builds_point_structs(monkeypatch):
    captured = {}

    class FakePointStruct:
        def __init__(self, *, id, vector, payload):
            self.id = id
            self.vector = vector
            self.payload = payload

    fake_models = SimpleNamespace(PointStruct=FakePointStruct)

    class FakeClient:
        def upsert(self, *, collection_name, points, wait):
            captured["collection_name"] = collection_name
            captured["point_ids"] = [point.id for point in points]
            captured["payloads"] = [point.payload for point in points]
            captured["wait"] = wait
            return {"status": "ok"}

    monkeypatch.setattr(QdrantService, "create_client", classmethod(lambda cls: FakeClient()))
    monkeypatch.setattr(QdrantService, "_get_models_module", classmethod(lambda cls: fake_models))

    response = QdrantService.upsert_points(
        "message-sending-rules",
        [
            {"id": "a", "vector": [0.1, 0.2], "payload": {"text": "hello"}},
            {"id": "b", "vector": [0.3, 0.4], "payload": {"text": "world"}},
        ],
    )

    assert response == {"status": "ok"}
    assert captured == {
        "collection_name": "message-sending-rules",
        "point_ids": ["a", "b"],
        "payloads": [{"text": "hello"}, {"text": "world"}],
        "wait": True,
    }


def test_search_points_uses_query_points_when_available(monkeypatch):
    captured = {}

    class FakeClient:
        def query_points(self, *, collection_name, query, limit, query_filter, with_payload):
            captured["collection_name"] = collection_name
            captured["query"] = query
            captured["limit"] = limit
            captured["query_filter"] = query_filter
            captured["with_payload"] = with_payload
            return SimpleNamespace(points=[SimpleNamespace(id="a"), SimpleNamespace(id="b")])

    monkeypatch.setattr(QdrantService, "create_client", classmethod(lambda cls: FakeClient()))
    monkeypatch.setattr(QdrantService, "build_match_filter", classmethod(lambda cls, filters: {"filters": filters}))

    results = QdrantService.search_points(
        "message-sending-rules",
        query_vector=[0.1, 0.2],
        limit=2,
        metadata_filters={"language": "ko"},
    )

    assert [item.id for item in results] == ["a", "b"]
    assert captured == {
        "collection_name": "message-sending-rules",
        "query": [0.1, 0.2],
        "limit": 2,
        "query_filter": {"filters": {"language": "ko"}},
        "with_payload": True,
    }
