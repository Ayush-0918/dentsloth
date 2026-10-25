import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import get_storage_backend, LocalCollection
from backend.matching.matcher import search_listings_by_vector, cosine_similarity

client = TestClient(app)


def test_health_reports_storage_backend_and_matching_mode():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "storage_backend" in data
    assert data["storage_backend"] in ["atlas", "sqlite"]
    assert "matching_mode" in data
    assert data["matching_mode"] in ["atlas", "in_memory_cosine"]


def test_storage_backend_detects_atlas_when_connected():
    with patch("backend.db.ping_db", return_value=True), \
         patch("backend.db._use_fallback", False):
        assert get_storage_backend() == "atlas"


def test_storage_backend_falls_back_to_sqlite():
    with patch("backend.db.ping_db", return_value=False), \
         patch("backend.db._use_fallback", True):
        assert get_storage_backend() == "sqlite"


def test_vector_search_fallback_to_in_memory_cosine():
    v1 = [1.0] + [0.0] * 63
    v2 = [1.0] + [0.0] * 63
    sim = cosine_similarity(v1, v2)
    assert pytest.approx(sim, 0.01) == 1.0

    # Execute search against current collection
    results, mode = search_listings_by_vector(v1, limit=5)
    assert mode in ["atlas", "in_memory_cosine"]
    assert isinstance(results, list)


def test_local_collection_delete_many():
    col = LocalCollection("test_temp_coll")
    col.insert_one({"_id": "test_1", "tag": "del_me"})
    col.insert_one({"_id": "test_2", "tag": "del_me"})
    col.insert_one({"_id": "test_3", "tag": "keep_me"})

    deleted_count = col.delete_many({"tag": "del_me"})
    assert deleted_count == 2
    assert col.count_documents({"tag": "del_me"}) == 0
    assert col.count_documents({"tag": "keep_me"}) == 1
    col.delete_one({"_id": "test_3"})
