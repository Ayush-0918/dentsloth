"""FastAPI endpoint for dental instrument identification via Gemma vision pipeline."""
import logging
import time
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from ..config import get_settings
from ..db import get_collection
from ..models import IdentifyResponse, AgentEvent
from ..llm.provider import get_llm_provider
from ..utils.image_ops import validate_and_strip_exif, ImageValidationError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["vision"])


@router.post(
    "/identify",
    response_model=IdentifyResponse,
    summary="Identify dental instruments from photo",
    description="Upload a photo of a single instrument or tray. Identifies instruments, grades condition, and applies safety guardrails.",
)
async def identify_instruments(file: UploadFile = File(...)):
    settings = get_settings()
    start_time = time.perf_counter()

    # Read uploaded file
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    # Validate format and strip EXIF
    try:
        clean_bytes, mime_type = validate_and_strip_exif(
            content,
            content_type=file.content_type,
            max_bytes=settings.max_upload_mb * 1024 * 1024,
        )
    except ImageValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )

    # Run inference pipeline
    provider = get_llm_provider()
    try:
        result = await provider.identify(
            image_bytes=clean_bytes,
            mime_type=mime_type,
            filename=file.filename,
        )
    except Exception as e:
        logger.error(f"Inference error in /api/identify: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision pipeline error: {str(e)}",
        )

    total_latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    result.latency_ms = total_latency_ms

    # Log latency to events collection
    event = AgentEvent(
        event_type="identify",
        latency_ms=total_latency_ms,
        payload={
            "filename": file.filename,
            "items_count": len(result.items),
            "can_list": result.can_list,
            "refusal_reason": result.refusal_reason,
            "demo": result.demo,
        },
    )
    try:
        get_collection("events").insert_one(event.model_dump())
    except Exception as dbe:
        logger.debug(f"Event logging skipped (DB degraded): {dbe}")

    return result
