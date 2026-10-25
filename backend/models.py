"""Pydantic models for DentSloth collections and API schemas."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ConditionGrade(str, Enum):
    A = "A"   # Excellent – barely used
    B = "B"   # Good – normal wear
    C = "C"   # Fair – functional but visibly used


class ListingStatus(str, Enum):
    draft = "draft"
    published = "published"
    sold = "sold"
    removed = "removed"


class Lifecycle(BaseModel):
    sterilization_cycles_est: Optional[int] = None
    last_sharpened: Optional[str] = None   # freeform date string


class IdentifiedItem(BaseModel):
    instrument_type: str = Field(..., description="Standard instrument identifier or catalog name")
    likely_brand: str = Field(default="unknown", description="Brand name if clearly identified, else unknown")
    material: str = Field(default="stainless_steel", description="Material specification, e.g. stainless steel")
    condition_grade: ConditionGrade = Field(default=ConditionGrade.B, description="Grade A, B, or C")
    visible_defects: List[str] = Field(default_factory=list, description="List of visible flaws, handle wear, rust spots, etc.")
    needs_sharpening: bool = Field(default=False, description="True if cutting edge/tip requires sharpening")
    is_single_use: bool = Field(default=False, description="True if single-use disposable item")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Model confidence score (0.0 to 1.0)")


class IdentifyResponse(BaseModel):
    items: List[IdentifiedItem] = Field(default_factory=list, description="All identified instruments in the image")
    notes: str = Field(default="", description="Clinical evaluation or identification notes")
    can_list: bool = Field(default=True, description="False if guardrails fail (single-use or low confidence)")
    refusal_reason: Optional[str] = Field(default=None, description="Human-readable reason for refusal")
    demo: bool = Field(default=False, description="True if served from demo cache")
    latency_ms: float = Field(default=0.0, description="Inference pipeline latency in milliseconds")


class Listing(BaseModel):
    instrument_type: str
    brand: str = "unknown"
    condition_grade: ConditionGrade
    age_years: float
    original_price_inr: Optional[float] = None
    suggested_price_inr: float
    price_low: float
    price_high: float
    description_en: str = ""
    description_hi: str = ""
    image_url: Optional[str] = None
    clinic_name: str
    city: str
    status: ListingStatus = ListingStatus.draft
    lifecycle: Lifecycle = Field(default_factory=Lifecycle)
    embedding: list[float] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    price_explanation: str = ""


class WishlistItem(BaseModel):
    buyer_name: str
    contact: str = ""
    wanted_text: str
    parsed: dict = Field(default_factory=dict)   # {types, max_budget_inr, city}
    embedding: list[float] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notified_listing_ids: list[str] = Field(default_factory=list)


class KitItem(BaseModel):
    listing_id: str
    instrument_type: str
    price: float
    condition_grade: str
    clinic_name: str


class Kit(BaseModel):
    buyer_request: str
    selected_listings: list[KitItem] = Field(default_factory=list)
    total_price: float = 0.0
    total_new_price_est: float = 0.0
    gaps: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentEvent(BaseModel):
    event_type: str        # identify | price | list | sloth_run | notification
    listing_id: Optional[str] = None
    wishlist_id: Optional[str] = None
    latency_ms: Optional[float] = None
    payload: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
