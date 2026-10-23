"""Pydantic models for DentSloth collections."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


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
