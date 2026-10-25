"""Starter Kit Builder API: AI assembly of custom instrument bundles within clinic budgets."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..db import get_collection
from ..models import Kit, KitItem, WishlistItem
from .listings import CATALOG, compute_text_embedding

logger = logging.getLogger(__name__)
router = APIRouter(tags=["kit"])

CATEGORY_MAP = {
    "exam": ["mouth_mirror", "dental_probe", "college_tweezers"],
    "diagnostic": ["mouth_mirror", "dental_probe", "college_tweezers"],
    "scaling": ["sickle_scaler", "gracey_curette"],
    "perio": ["sickle_scaler", "gracey_curette", "periodontal_probe"],
    "extraction": ["extraction_forceps_upper_anterior", "straight_elevator"],
    "surgery": ["extraction_forceps_upper_anterior", "straight_elevator", "periosteal_elevator"],
    "restorative": ["amalgam_condenser", "carver_cleoid_discoid"],
}


class KitRequest(BaseModel):
    request: str = Field(..., description="Plain-language description of clinic needs, e.g. 'general practice exam + extraction set'")
    budget: float = Field(..., ge=100.0, description="Maximum budget in INR")


@router.post(
    "/kit",
    summary="Assemble a Starter Kit within budget",
    description="Greedy / knapsack bundle optimizer: selects best used listings to meet equipment needs without exceeding budget, calculates savings vs new retail, and auto-wishlists gaps.",
)
async def build_starter_kit(payload: KitRequest):
    req_lower = payload.request.lower()

    # Determine required categories
    needed_types = []
    for cat_name, types in CATEGORY_MAP.items():
        if cat_name in req_lower:
            needed_types.extend(types)

    if not needed_types:
        # Default starter practice kit
        needed_types = ["mouth_mirror", "dental_probe", "sickle_scaler", "gracey_curette", "straight_elevator"]

    # Deduplicate preserving order
    needed_types = list(dict.fromkeys(needed_types))

    # Fetch available published listings
    coll = get_collection("listings")
    available_listings = list(coll.find({"status": "published"}))

    selected_items: List[KitItem] = []
    current_cost = 0.0
    total_new_price_est = 0.0
    gaps: List[str] = []

    for itype in needed_types:
        # Filter available candidates
        candidates = [
            l for l in available_listings
            if l.get("instrument_type") == itype and l.get("_id") not in [s.listing_id for s in selected_items]
        ]
        # Sort by condition (A > B > C) and price
        candidates.sort(
            key=lambda c: (
                0 if c.get("condition_grade") == "A" else (1 if c.get("condition_grade") == "B" else 2),
                c.get("suggested_price_inr", 999999),
            )
        )

        matched = None
        for cand in candidates:
            price = float(cand.get("suggested_price_inr", 0))
            if current_cost + price <= payload.budget:
                matched = cand
                break

        if matched:
            price = float(matched.get("suggested_price_inr", 0))
            current_cost += price
            selected_items.append(
                KitItem(
                    listing_id=str(matched.get("_id")),
                    instrument_type=str(matched.get("instrument_type")),
                    price=price,
                    condition_grade=str(matched.get("condition_grade")),
                    clinic_name=str(matched.get("clinic_name", "Partner Clinic")),
                )
            )
            # Add illustrative new price
            orig_p = float(matched.get("original_price_inr") or price * 1.5)
            total_new_price_est += orig_p
        else:
            cat_entry = CATALOG.get(itype, {})
            name_en = cat_entry.get("name_en", itype.replace("_", " ").title())
            gaps.append(name_en)
            if "new_price_range_inr" in cat_entry:
                total_new_price_est += sum(cat_entry["new_price_range_inr"]) / 2.0

    # Auto-add gaps to wishlist if any
    if gaps:
        gap_text = f"Kit builder gaps: {', '.join(gaps)} (from request: '{payload.request}')"
        wishlist_doc = WishlistItem(
            buyer_name="Starter Kit Seeker",
            wanted_text=gap_text,
            parsed={"types": gaps, "max_budget_inr": payload.budget - current_cost},
            embedding=compute_text_embedding(gap_text),
        )
        try:
            get_collection("wishlists").insert_one(wishlist_doc.model_dump())
        except Exception:
            pass

    return {
        "selected_listings": [s.model_dump() for s in selected_items],
        "total_price": round(current_cost, 2),
        "total_new_price_est": round(total_new_price_est, 2),
        "savings_inr": round(max(0.0, total_new_price_est - current_cost), 2),
        "gaps": gaps,
    }
