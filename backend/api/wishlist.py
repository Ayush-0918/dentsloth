"""Wishlist API: plain-language dental equipment request parsing and registration."""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..db import get_collection
from ..models import WishlistItem, AgentEvent
from .listings import compute_text_embedding

logger = logging.getLogger(__name__)
router = APIRouter(tags=["wishlist"])

KNOWN_INSTRUMENT_KEYWORDS = [
    "mirror", "probe", "explorer", "scaler", "curette", "forceps",
    "elevator", "handpiece", "condenser", "carver", "pliers", "tweezers"
]


class WishlistCreate(BaseModel):
    buyer_name: str = Field(..., description="Dentist or clinic buyer name")
    contact: str = Field(default="", description="Contact email or phone")
    wanted_text: str = Field(..., description="Plain-language description of instruments wanted")
    city: str = Field(default="Mumbai", description="Buyer preferred city or delivery hub")
    max_budget_inr: Optional[float] = Field(default=None, description="Maximum budget in INR")


@router.post(
    "/wishlist",
    summary="Create a plain-language equipment wishlist",
    description="Registers buyer demand. Gemma parses keywords and budget constraints for automated Sloth Run matching.",
)
async def create_wishlist(payload: WishlistCreate):
    text_lower = payload.wanted_text.lower()
    matched_types = [kw for kw in KNOWN_INSTRUMENT_KEYWORDS if kw in text_lower]
    if not matched_types:
        matched_types = ["general_instruments"]

    parsed_info = {
        "types": matched_types,
        "max_budget_inr": payload.max_budget_inr or 15000.0,
        "city": payload.city,
    }

    embed = compute_text_embedding(f"{payload.wanted_text} {payload.city} {' '.join(matched_types)}")

    item = WishlistItem(
        buyer_name=payload.buyer_name,
        contact=payload.contact,
        wanted_text=payload.wanted_text,
        parsed=parsed_info,
        embedding=embed,
        notified_listing_ids=[],
    )

    res = get_collection("wishlists").insert_one(item.model_dump())
    item_dict = item.model_dump()
    item_dict["_id"] = res.inserted_id

    # Log event
    event = AgentEvent(
        event_type="wishlist",
        wishlist_id=str(res.inserted_id),
        payload={"buyer": payload.buyer_name, "types": matched_types, "budget": parsed_info["max_budget_inr"]},
    )
    try:
        get_collection("events").insert_one(event.model_dump())
    except Exception:
        pass

    return {"id": res.inserted_id, "wishlist": item_dict}
