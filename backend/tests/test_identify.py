"""Phase 2 Acceptance Tests for Gemma Vision Pipeline."""
import io
import json
import os
import pytest
from PIL import Image
import piexif
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import IdentifiedItem, ConditionGrade
from backend.llm.provider import (
    OllamaProvider,
    parse_and_validate_json,
    apply_guardrails,
    DemoVisionProvider,
)
from backend.utils.image_ops import validate_and_strip_exif, ImageValidationError

client = TestClient(app)
SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sample_images")


def create_test_image_bytes(with_exif: bool = True) -> bytes:
    """Helper to generate a clean JPEG in memory with optional EXIF."""
    img = Image.new("RGB", (100, 100), color=(200, 210, 220))
    buf = io.BytesIO()
    if with_exif:
        zeroth = {piexif.ImageIFD.Make: b"TestCamera", piexif.ImageIFD.Software: b"SecretSoftware"}
        gps = {piexif.GPSIFD.GPSLatitude: ((18, 1), (31, 1), (0, 1))}
        exif_bytes = piexif.dump({"0th": zeroth, "GPS": gps})
        img.save(buf, format="JPEG", exif=exif_bytes)
    else:
        img.save(buf, format="JPEG")
    return buf.getvalue()


# ── Acceptance Check 1: 6+ sample images processed ────────────────────────────
def test_sample_images_count_and_processing():
    """Verify at least 6 sample images exist and all process successfully via endpoint."""
    assert os.path.exists(SAMPLES_DIR), "sample_images directory must exist"
    sample_files = [f for f in os.listdir(SAMPLES_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    assert len(sample_files) >= 6, f"Expected at least 6 sample images, found {len(sample_files)}"

    for fname in sample_files:
        fpath = os.path.join(SAMPLES_DIR, fname)
        with open(fpath, "rb") as f:
            res = client.post(
                "/api/identify",
                files={"file": (fname, f.read(), "image/jpeg")},
            )
        assert res.status_code == 200, f"Failed for sample {fname}: {res.text}"
        data = res.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert "can_list" in data
        assert "latency_ms" in data


# ── Acceptance Check 2: Single-use item refusal guardrail ──────────────────────
def test_single_use_item_refusal():
    """Single-use disposable instruments must trigger refusal guardrail."""
    sample_path = os.path.join(SAMPLES_DIR, "disposable_needle_syringe.jpg")
    with open(sample_path, "rb") as f:
        res = client.post(
            "/api/identify",
            files={"file": ("disposable_needle_syringe.jpg", f.read(), "image/jpeg")},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["can_list"] is False
    assert data["refusal_reason"] is not None
    assert "single-use" in data["refusal_reason"].lower() or "disposable" in data["refusal_reason"].lower()


# ── Acceptance Check 3: Low confidence item refusal guardrail ─────────────────
def test_low_confidence_refusal():
    """Confidence below 0.40 must trigger retake photo refusal."""
    sample_path = os.path.join(SAMPLES_DIR, "blurry_unknown_object.jpg")
    with open(sample_path, "rb") as f:
        res = client.post(
            "/api/identify",
            files={"file": ("blurry_unknown_object.jpg", f.read(), "image/jpeg")},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["can_list"] is False
    assert data["refusal_reason"] is not None
    assert "retake" in data["refusal_reason"].lower() or "confidence" in data["refusal_reason"].lower()


# ── Acceptance Check 4: Multi-instrument tray photo ───────────────────────────
def test_multi_instrument_tray_identification():
    """Tray photo containing multiple instruments returns all items."""
    sample_path = os.path.join(SAMPLES_DIR, "tray_instruments_multi.jpg")
    with open(sample_path, "rb") as f:
        res = client.post(
            "/api/identify",
            files={"file": ("tray_instruments_multi.jpg", f.read(), "image/jpeg")},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["can_list"] is True
    assert len(data["items"]) == 3
    types = [it["instrument_type"] for it in data["items"]]
    assert "mouth_mirror" in types
    assert "dental_probe" in types


# ── Acceptance Check 5: Invalid JSON retry and error handling ──────────────────
def test_json_parser_resilience():
    """Test parse_and_validate_json handles markdown code fences, whitespace, and invalid text."""
    # Markdown wrapped JSON
    markdown_json = '```json\n{"items": [{"instrument_type": "probe", "condition_grade": "A", "confidence": 0.9}], "notes": "good"}\n```'
    parsed = parse_and_validate_json(markdown_json)
    assert parsed["items"][0]["instrument_type"] == "probe"

    # Conversational prefix before JSON
    conversational = 'Here is the identified instrument in JSON format:\n{"items": [{"instrument_type": "scaler", "condition_grade": "B", "confidence": 0.85}], "notes": "scaler found"}'
    parsed2 = parse_and_validate_json(conversational)
    assert parsed2["items"][0]["instrument_type"] == "scaler"

    # Completely broken JSON
    with pytest.raises(Exception):
        parse_and_validate_json("I cannot identify this instrument. It is not JSON.")


@pytest.mark.asyncio
async def test_ollama_provider_retry_on_invalid_json(monkeypatch):
    """Verify OllamaProvider retries once on invalid JSON and raises informative error if retry fails."""
    provider = OllamaProvider(base_url="http://mock-ollama:11434", model="gemma3:4b")

    attempts = 0

    async def mock_post(self, url, *args, **kwargs):
        nonlocal attempts
        attempts += 1
        class MockResponse:
            def raise_for_status(self):
                pass
            def json(self):
                # Return non-JSON string on both attempts
                return {"message": {"content": "This is definitely not json."}}
        return MockResponse()

    # Test that retry was executed
    from httpx import AsyncClient
    monkeypatch.setattr(AsyncClient, "post", mock_post)

    with pytest.raises(RuntimeError) as exc_info:
        await provider.identify(b"fake_image_bytes")
    assert "failed to produce valid JSON" in str(exc_info.value)
    assert attempts == 2, f"Expected 2 attempts (initial + 1 retry), got {attempts}"


# ── Acceptance Check 6: EXIF stripping ────────────────────────────────────────
def test_exif_metadata_stripped():
    """Verify that private EXIF GPS and camera tags are stripped from output image."""
    raw_with_exif = create_test_image_bytes(with_exif=True)
    # Confirm raw bytes contain EXIF
    exif_raw = piexif.load(raw_with_exif)
    assert "0th" in exif_raw and len(exif_raw["0th"]) > 0

    clean_bytes, mime = validate_and_strip_exif(raw_with_exif)
    assert mime == "image/jpeg"
    # Confirm clean bytes have no EXIF
    exif_clean = piexif.load(clean_bytes)
    assert len(exif_clean.get("0th", {})) == 0
    assert len(exif_clean.get("GPS", {})) == 0


# ── Acceptance Check 7: File size limits ──────────────────────────────────────
def test_max_upload_size_validation():
    """Files exceeding max size limit are rejected with HTTP 400."""
    huge_bytes = b"0" * (11 * 1024 * 1024)  # 11 MB
    res = client.post(
        "/api/identify",
        files={"file": ("too_big.jpg", huge_bytes, "image/jpeg")},
    )
    assert res.status_code == 400
    assert "exceeds maximum allowed limit" in res.json()["detail"]


# ── Acceptance Check 8: DEMO_MODE works offline ───────────────────────────────
def test_demo_mode_offline():
    """DEMO_MODE serves cached and deterministic responses completely offline."""
    cache_path = os.path.join(SAMPLES_DIR, "demo_cache.json")
    demo_provider = DemoVisionProvider(cache_file=cache_path)

    # Test known sample
    import asyncio
    res = asyncio.run(demo_provider.identify(b"irrelevant_bytes", filename="mouth_mirror_grade_a.jpg"))
    assert res.demo is True
    assert res.can_list is True
    assert res.items[0].instrument_type == "mouth_mirror"
    assert res.items[0].likely_brand == "Hu-Friedy"

    # Test unknown sample in offline demo mode
    res_unknown = asyncio.run(demo_provider.identify(b"unknown_bytes", filename="random_clinic_photo.jpg"))
    assert res_unknown.demo is True
    assert res_unknown.can_list is True
    assert len(res_unknown.items) >= 1
