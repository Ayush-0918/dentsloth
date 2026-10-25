"""Phase 3 Acceptance Tests for TabPFN Pricing Agent and Sanity Rules."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.pricing.tabpfn_model import (
    TabPFNPricingAgent,
    classify_brand,
    round_to_50,
)

client = TestClient(app)


# ── Sanity Rule Test 1: Rounding to nearest Rs 50 ─────────────────────────────
def test_round_to_50():
    assert round_to_50(502.4) == 500
    assert round_to_50(526.0) == 550
    assert round_to_50(548.9) == 550
    assert round_to_50(574.0) == 550
    assert round_to_50(576.0) == 600
    assert round_to_50(20.0) == 50  # Minimum floor


# ── Sanity Rule Test 2: Brand tier classification ─────────────────────────────
def test_brand_tier_classification():
    assert classify_brand("Hu-Friedy") == "premium"
    assert classify_brand("NSK") == "premium"
    assert classify_brand("Kohler") == "premium"
    assert classify_brand("GDC") == "midrange"
    assert classify_brand("Dentsply") == "midrange"
    assert classify_brand("API") == "midrange"
    assert classify_brand("Generic") == "economy"
    assert classify_brand("Budget Plus") == "economy"
    assert classify_brand("unknown") == "economy"
    assert classify_brand("") == "economy"


# ── Sanity Rule Test 3: 85% Ceiling Cap & Floor Protection ────────────────────
def test_sanity_rules_cap_and_floor():
    agent = TabPFNPricingAgent()

    # Case A: Pristine condition brand new item must NOT exceed 85% of new price
    original_price = 1000.0
    cap_limit = round(original_price * 0.85)  # 850
    pred = agent.predict(
        instrument_type="mouth_mirror",
        brand="Hu-Friedy",
        condition_grade="A",
        age_years=0.1,
        original_price_inr=original_price,
    )
    assert pred["suggested_price_inr"] <= cap_limit
    assert pred["price_high"] <= cap_limit
    assert pred["price_low"] >= 50
    assert pred["price_low"] <= pred["suggested_price_inr"] <= pred["price_high"]

    # Case B: Very old heavily used item must respect minimum floor
    pred_old = agent.predict(
        instrument_type="mouth_mirror",
        brand="generic",
        condition_grade="C",
        age_years=15.0,
        original_price_inr=500.0,
    )
    floor_limit = max(50, round(500.0 * 0.10))  # 50
    assert pred_old["suggested_price_inr"] >= floor_limit
    assert pred_old["price_low"] >= floor_limit
    assert pred_old["price_low"] <= pred_old["suggested_price_inr"] <= pred_old["price_high"]


# ── Acceptance Check: POST /api/price endpoint ────────────────────────────────
def test_price_endpoint():
    res = client.post(
        "/api/price",
        json={
            "instrument_type": "mouth_mirror",
            "brand": "Hu-Friedy",
            "condition_grade": "B",
            "age_years": 2.5,
            "original_price_inr": 800.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "suggested_price_inr" in data
    assert "price_low" in data
    assert "price_high" in data
    assert "explanation" in data
    assert "brand_tier" in data

    # Verify uncertainty interval order
    assert data["price_low"] <= data["suggested_price_inr"] <= data["price_high"]
    # Verify quantization to 50
    assert data["suggested_price_inr"] % 50 == 0
    assert data["price_low"] % 50 == 0
    assert data["price_high"] % 50 == 0
    # Verify 85% cap
    assert data["suggested_price_inr"] <= round(800.0 * 0.85)


def test_price_endpoint_missing_original_price_catalog_fallback():
    """Missing original price defaults to instrument_catalog midpoint."""
    res = client.post(
        "/api/price",
        json={
            "instrument_type": "sickle_scaler",
            "brand": "GDC",
            "condition_grade": "B",
            "age_years": 1.5,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["original_price_inr"] > 0
    assert data["price_low"] <= data["suggested_price_inr"] <= data["price_high"]
