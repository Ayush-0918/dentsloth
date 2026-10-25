"""FastAPI endpoint for fair resale price estimation via TabPFN pricing agent."""
import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..db import get_collection
from ..models import AgentEvent
from ..pricing.tabpfn_model import get_pricing_agent

logger = logging.getLogger(__name__)
router = APIRouter(tags=["pricing"])


class PriceRequest(BaseModel):
    instrument_type: str = Field(..., description="Standard instrument identifier, e.g. mouth_mirror, sickle_scaler")
    brand: str = Field(default="unknown", description="Brand name, e.g. Hu-Friedy, GDC, Dentsply, or unknown")
    condition_grade: str = Field(default="B", description="Condition grade: A, B, or C")
    age_years: float = Field(default=2.0, ge=0.0, description="Instrument age in years")
    original_price_inr: Optional[float] = Field(default=None, description="Original new price in INR if known")
    sterilization_cycles_est: Optional[float] = Field(default=None, description="Estimated autoclave sterilization cycles")


class PriceResponse(BaseModel):
    suggested_price_inr: int = Field(..., description="Fair suggested resale price in INR (rounded to nearest 50)")
    price_low: int = Field(..., description="Lower quantile bound of fair market value")
    price_high: int = Field(..., description="Upper quantile bound of fair market value")
    explanation: str = Field(..., description="Human-readable explanation citing comparables and sanity rules")
    original_price_inr: float = Field(..., description="Reference original retail price used for sanity caps")
    brand_tier: str = Field(..., description="Classified brand tier: premium, midrange, or economy")


@router.post(
    "/price",
    response_model=PriceResponse,
    summary="Estimate fair resale price using TabPFN",
    description="Calculates fair resale value and quantile bounds from TabPFN with clinical sanity checks (85% cap, floor, ₹50 quantization).",
)
async def estimate_price(req: PriceRequest):
    t0 = time.perf_counter()
    agent = get_pricing_agent()
    try:
        pred = agent.predict(
            instrument_type=req.instrument_type,
            brand=req.brand,
            condition_grade=req.condition_grade,
            age_years=req.age_years,
            original_price_inr=req.original_price_inr,
            sterilization_cycles_est=req.sterilization_cycles_est,
        )
    except Exception as e:
        logger.error(f"TabPFN pricing prediction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pricing model inference error: {str(e)}",
        )

    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    # Log to events collection
    event = AgentEvent(
        event_type="price",
        latency_ms=latency_ms,
        payload={
            "instrument_type": req.instrument_type,
            "brand": req.brand,
            "condition_grade": req.condition_grade,
            "suggested_price_inr": pred["suggested_price_inr"],
            "price_low": pred["price_low"],
            "price_high": pred["price_high"],
        },
    )
    try:
        get_collection("events").insert_one(event.model_dump())
    except Exception as dbe:
        logger.debug(f"Event logging skipped: {dbe}")

    return PriceResponse(**pred)
