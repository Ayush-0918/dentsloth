import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.tracing import trace_transaction, trace_span

client = TestClient(app)


def test_debug_trace_test_disabled_by_default():
    with patch("backend.main.get_settings") as mock_settings:
        mock_settings.return_value.enable_debug = False
        res = client.get("/api/debug/trace-test")
        assert res.status_code == 404


def test_debug_trace_test_enabled_triggers_spans():
    with patch("backend.main.get_settings") as mock_settings:
        mock_settings.return_value.enable_debug = True
        mock_settings.return_value.sentry_dsn = ""
        mock_settings.return_value.is_demo = False
        mock_settings.return_value.llm_provider = "hosted"
        mock_settings.return_value.tabpfn_mode = "api"

        res = client.get("/api/debug/trace-test")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "trace_generated"
        assert data["transaction"] == "lazy_listing"
        assert "image_sanitize" in data["spans"]
        assert "gemma_identify" in data["spans"]
        assert "tabpfn_price" in data["spans"]
        assert "gemma_listing_text" in data["spans"]
        assert "db_write" in data["spans"]


def test_tracing_context_managers_noop_when_dsn_empty():
    with trace_transaction(name="test_txn") as txn:
        txn.set_attribute("key", "val")
        with trace_span(name="test_span") as span:
            span.set_attribute("inner_key", "inner_val")
    # Must succeed without throwing
    assert True
