"""Listings API: automated listing generation, publishing, and marketplace retrieval."""
import json
import logging
import os
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query, status, Request
from pydantic import BaseModel, Field

from ..db import get_collection
from ..config import get_settings
from ..models import Listing, ListingStatus, ConditionGrade, Lifecycle, AgentEvent
from ..llm.provider import get_llm_provider
from ..pricing.tabpfn_model import get_pricing_agent
from ..utils.image_ops import validate_and_strip_exif

logger = logging.getLogger(__name__)
router = APIRouter(tags=["listings"])

# Catalog lookup
CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "instrument_catalog.json")
CATALOG: Dict[str, Any] = {}
if os.path.exists(CATALOG_PATH):
    try:
        with open(CATALOG_PATH, "r") as f:
            CATALOG = {item["id"]: item for item in json.load(f).get("instruments", [])}
    except Exception as e:
        logger.warning(f"Failed to load catalog: {e}")


def get_catalog_names(type_id: str) -> tuple[str, str]:
    clean = type_id.lower().replace(" ", "_").replace("-", "_")
    cat = CATALOG.get(clean)
    if cat:
        return cat.get("name_en", type_id.title()), cat.get("name_hi", type_id.title())
    return type_id.replace("_", " ").title(), type_id.replace("_", " ").title()


def compute_text_embedding(text: str) -> list[float]:
    """Lightweight deterministic semantic embedding for local cosine search."""
    import hashlib
    # 64-dimensional normalized bag-of-words / hash embedding
    vec = [0.0] * 64
    for word in text.lower().split():
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = h % 64
        vec[idx] += 1.0
    norm = sum(x * x for x in vec) ** 0.5
    return [round(x / norm, 4) for x in vec] if norm > 0 else vec


@router.post(
    "/listings/auto",
    summary="Auto-generate draft listing from photo",
    description="Full lazy seller loop: Image upload -> Identify -> Price -> Bilingual description -> Saved draft.",
)
async def auto_create_listing(request: Request):
    settings = get_settings()
    t0 = time.perf_counter()

    content_type = request.headers.get("content-type", "")
    identified_items = []
    clinic_name = "Sunrise Dental Clinic"
    city = "Pune"
    age_years = 2.0
    suggested_price_override = None

    if "application/json" in content_type:
        body = await request.json()
        clinic_name = body.get("clinic_name", clinic_name)
        city = body.get("city", city)
        age_years = float(body.get("age_years", age_years))
        suggested_price_override = body.get("suggested_price_inr")

        from ..models import IdentifiedItem
        cond_val = str(body.get("condition_grade", "B")).upper()
        if cond_val not in ["A", "B", "C"]:
            cond_val = "B"
        identified_items = [
            IdentifiedItem(
                instrument_type=body.get("instrument_type", "mouth_mirror"),
                likely_brand=body.get("likely_brand") or body.get("brand") or "unknown",
                condition_grade=ConditionGrade(cond_val),
                confidence=float(body.get("confidence", 0.90)),
                visible_defects=body.get("visible_defects", []),
            )
        ]
    else:
        form = await request.form()
        file = form.get("file")
        clinic_name = str(form.get("clinic_name") or clinic_name)
        city = str(form.get("city") or city)
        age_years = float(form.get("age_years") or age_years)
        instrument_type = form.get("instrument_type")
        brand = form.get("brand")
        condition_grade = form.get("condition_grade") or "B"

        if file and hasattr(file, "read"):
            content = await file.read()
            if content:
                clean_bytes, mime = validate_and_strip_exif(content, getattr(file, "content_type", None))
                provider = get_llm_provider()
                id_res = await provider.identify(clean_bytes, mime, getattr(file, "filename", None))
                if not id_res.can_list:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=id_res.refusal_reason or "Instrument could not be approved for listing.",
                    )
                identified_items = id_res.items

        if not identified_items:
            from ..models import IdentifiedItem
            cond_val = str(condition_grade).upper()
            if cond_val not in ["A", "B", "C"]:
                cond_val = "B"
            identified_items = [
                IdentifiedItem(
                    instrument_type=str(instrument_type or "mouth_mirror"),
                    likely_brand=str(brand or "unknown"),
                    condition_grade=ConditionGrade(cond_val),
                    confidence=0.90,
                )
            ]

    pricing_agent = get_pricing_agent()
    created_drafts = []

    for item in identified_items:
        # Step 2: Price via TabPFN
        price_res = pricing_agent.predict(
            instrument_type=item.instrument_type,
            brand=item.likely_brand,
            condition_grade=item.condition_grade.value,
            age_years=age_years,
        )

        name_en, name_hi = get_catalog_names(item.instrument_type)
        brand_label = item.likely_brand if item.likely_brand != "unknown" else "Professional"

        # Step 3: Bilingual listing generation
        defects = ", ".join(item.visible_defects) if item.visible_defects else "No major structural defects"
        desc_en = (
            f"{brand_label} {name_en} (Grade {item.condition_grade.value}). "
            f"Sterilization inspected: {defects}. Professional autoclave-ready stainless steel. "
            f"{price_res['explanation']}"
        )
        desc_hi = (
            f"{brand_label} {name_hi} (ग्रेड {item.condition_grade.value})। "
            f"नैदानिक पुनः उपयोग हेतु जाँचा गया: {defects}। ऑटोकलेव के लिए सुरक्षित स्टेनलेस स्टील।"
        )

        embed = compute_text_embedding(f"{name_en} {name_hi} {brand_label} {city}")

        suggested_val = float(suggested_price_override) if suggested_price_override is not None else price_res["suggested_price_inr"]
        listing = Listing(
            instrument_type=item.instrument_type,
            brand=item.likely_brand,
            condition_grade=item.condition_grade,
            age_years=age_years,
            original_price_inr=price_res["original_price_inr"],
            suggested_price_inr=suggested_val,
            price_low=price_res["price_low"],
            price_high=price_res["price_high"],
            description_en=desc_en,
            description_hi=desc_hi,
            clinic_name=clinic_name,
            city=city,
            status=ListingStatus.draft,
            price_explanation=price_res["explanation"],
            embedding=embed,
            lifecycle=Lifecycle(
                sterilization_cycles_est=int(round(age_years * 50)),
                last_sharpened="Recently inspected",
            ),
        )

        # Step 4: Save draft
        res = get_collection("listings").insert_one(listing.model_dump())
        listing_dict = listing.model_dump()
        listing_dict["_id"] = res.inserted_id
        created_drafts.append(listing_dict)

    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    primary = created_drafts[0]

    # Log event
    event = AgentEvent(
        event_type="list",
        listing_id=str(primary["_id"]),
        latency_ms=latency_ms,
        payload={"count": len(created_drafts), "status": "draft"},
    )
    try:
        get_collection("events").insert_one(event.model_dump())
    except Exception:
        pass

    return {"id": primary["_id"], "draft": primary, "all_drafts": created_drafts}


@router.post("/listings/{listing_id}/publish")
async def publish_listing(listing_id: str):
    """Publish a draft listing to the active marketplace."""
    coll = get_collection("listings")
    doc = coll.find_one({"_id": listing_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Listing not found")

    coll.update_one({"_id": listing_id}, {"$set": {"status": "published"}})
    return {"id": listing_id, "status": "published"}


@router.get("/listings")
async def get_listings(
    instrument_type: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = "published",
    condition: Optional[str] = None,
    max_price: Optional[float] = None,
):
    """Search and filter marketplace listings."""
    filt = {}
    if status and status != "all":
        filt["status"] = status
    if instrument_type:
        filt["instrument_type"] = instrument_type
    if city:
        filt["city"] = city
    if condition:
        filt["condition_grade"] = condition

    cursor = get_collection("listings").find(filt)
    all_items = list(cursor)

    if max_price:
        all_items = [i for i in all_items if i.get("suggested_price_inr", 0) <= max_price]

    return {"listings": all_items}


@router.get("/listings/{listing_id}")
async def get_single_listing(listing_id: str):
    doc = get_collection("listings").find_one({"_id": listing_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Listing not found")
    return doc
