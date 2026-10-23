"""Basic health endpoint test."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_health_endpoint():
    with patch("backend.db.get_client") as mock_client:
        mock_db = MagicMock()
        mock_db.command.return_value = {"ok": 1}
        mock_client.return_value = {"dentsloth": mock_db}

        from backend.main import app
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "demo_mode" in data
        assert "llm_provider" in data
