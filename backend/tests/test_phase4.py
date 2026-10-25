"""Phase 4 Acceptance Tests: Listings, Wishlist, Starter Kit, Sloth Run, and Dashboard."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import get_collection
from scripts.sloth_run import run_sloth

client = TestClient(app)


def test_auto_create_listing_and_publish():
    # 1. Auto create listing
    res = client.post(
        "/api/listings/auto",
        data={
            "instrument_type": "mouth_mirror",
            "brand": "Hu-Friedy",
            "condition_grade": "A",
            "age_years": 1.0,
            "clinic_name": "Dental Care Clinic",
            "city": "Bengaluru",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "id" in data
    assert "draft" in data
    draft = data["draft"]
    assert draft["status"] == "draft"
    assert draft["instrument_type"] == "mouth_mirror"
    assert draft["suggested_price_inr"] > 0
    assert "description_en" in draft
    assert "description_hi" in draft
    listing_id = data["id"]

    # 2. Publish listing
    pub_res = client.post(f"/api/listings/{listing_id}/publish")
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "published"

    # 3. Query listings with filter
    list_res = client.get("/api/listings?instrument_type=mouth_mirror&city=Bengaluru")
    assert list_res.status_code == 200
    listings = list_res.json()["listings"]
    found = [l for l in listings if str(l.get("_id")) == str(listing_id)]
    assert len(found) == 1
    assert found[0]["status"] == "published"


def test_wishlist_creation():
    res = client.post(
        "/api/wishlist",
        json={
            "buyer_name": "Dr. Sharma",
            "contact": "drsharma@example.com",
            "wanted_text": "Looking for Hu-Friedy mouth mirror and sickle scaler under 1500",
            "city": "Bengaluru",
            "max_budget_inr": 1500.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert "wishlist" in data
    assert data["wishlist"]["buyer_name"] == "Dr. Sharma"
    assert "mirror" in data["wishlist"]["parsed"]["types"]


def test_starter_kit_builder():
    res = client.post(
        "/api/kit",
        json={
            "request": "need basic exam set for general practice",
            "budget": 5000.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "selected_listings" in data
    assert "total_price" in data
    assert "savings_inr" in data
    assert "gaps" in data
    assert data["total_price"] <= 5000.0


def test_sloth_run_idempotency_and_summary():
    # Run sloth run first time
    summary_1 = run_sloth()
    assert "Morning Sloth Summary" in summary_1

    # Run sloth run second time - must be idempotent (0 new duplicate notifications)
    events_coll = get_collection("events")
    count_before = events_coll.count_documents({"event_type": "notification"})
    summary_2 = run_sloth()
    count_after = events_coll.count_documents({"event_type": "notification"})

    assert count_after == count_before, "Sloth run must be idempotent: no duplicate notifications on rerun"


def test_dashboard_endpoint():
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "sloth_run" in data
    assert "listings" in data
    assert "matches" in data
    assert "lazy_payoff" in data
    assert "measured_median_s" in data["lazy_payoff"]
