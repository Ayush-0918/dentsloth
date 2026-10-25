"""DentSloth FastAPI application entry-point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .db import ping_db, get_storage_backend
from .tracing import init_sentry, trace_transaction, trace_span
from .api import identify, price, listings, wishlist, kit, dashboard

logging.basicConfig(level=get_settings().log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    logger.info(f"DentSloth starting | env={settings.app_env} demo_mode={settings.is_demo}")
    init_sentry()
    if ping_db():
        logger.info("DB ping OK")
    else:
        logger.warning("DB not reachable – starting in degraded mode (OK for demo)")

    # Auto-seed on startup if listings store is empty
    try:
        from .db import get_collection
        col = get_collection("listings")
        if col.count_documents() == 0:
            logger.info("Listings store is empty; auto-seeding demo listings...")
            from scripts.seed_demo_listings import seed
            seed()
    except Exception as e:
        logger.warning(f"Auto-seed check encountered error: {e}")
    yield
    # Shutdown
    logger.info("DentSloth shutting down")


settings = get_settings()
app = FastAPI(
    title="DentSloth API",
    description="Snap one photo of a dental instrument. The sloth does the rest.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
@app.get("/api/health", tags=["meta"])
async def health():
    """Health check endpoint."""
    db_ok = ping_db()
    storage_type = get_storage_backend()
    from .matching.matcher import check_atlas_vector_search_ready
    vector_ready = check_atlas_vector_search_ready()
    return {
        "status": "ok",
        "demo_mode": settings.is_demo,
        "db": "ok" if db_ok else "degraded",
        "storage_backend": storage_type,
        "matching_mode": "atlas" if vector_ready else "in_memory_cosine",
        "llm_provider": settings.llm_provider,
    }


# Register routers
app.include_router(identify.router, prefix="/api")
app.include_router(price.router, prefix="/api")
app.include_router(listings.router, prefix="/api")
app.include_router(wishlist.router, prefix="/api")
app.include_router(kit.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/api/debug/trace-test", tags=["debug"])
async def debug_trace_test():
    """Generates a sample Sentry agent trace when ENABLE_DEBUG=true."""
    from fastapi import HTTPException
    settings = get_settings()
    if not settings.enable_debug:
        raise HTTPException(status_code=404, detail="Debug endpoints are disabled (set ENABLE_DEBUG=true).")

    with trace_transaction(name="lazy_listing", op="ai.agent") as parent:
        parent.set_attribute("flow", "debug_sample_listing")
        parent.set_attribute("demo_mode", settings.is_demo)

        with trace_span(name="image_sanitize", op="ai.sanitize") as s1:
            s1.set_attribute("exif_stripped", True)
            s1.set_attribute("dimensions", "1200x800")
            s1.set_attribute("latency_ms", 14)

        with trace_span(name="gemma_identify", op="ai.inference") as s2:
            s2.set_attribute("provider", settings.llm_provider)
            s2.set_attribute("model_name", settings.ollama_model if settings.llm_provider == "ollama" else "gemini-2.0-flash")
            s2.set_attribute("confidence", 0.94)
            s2.set_attribute("can_list", True)
            s2.set_attribute("token_counts", {"prompt_tokens": 148, "completion_tokens": 92})
            s2.set_attribute("cost", "0 for local; hosted per Google AI Studio free tier/quota")

        with trace_span(name="tabpfn_price", op="ai.pricing") as s3:
            s3.set_attribute("mode", settings.tabpfn_mode)
            s3.set_attribute("instrument_type", "sickle_scaler")
            s3.set_attribute("condition_grade", "B")
            s3.set_attribute("suggested_price_inr", 400)
            s3.set_attribute("price_range", "₹350 - ₹480")
            s3.set_attribute("sanity_cap_applied", True)

        with trace_span(name="gemma_listing_text", op="ai.synthesis") as s4:
            s4.set_attribute("languages", ["en", "hi"])
            s4.set_attribute("latency_ms", 210)

        with trace_span(name="db_write", op="db.insert") as s5:
            s5.set_attribute("storage_backend", get_storage_backend())
            s5.set_attribute("collection", "listings")

    return {
        "status": "trace_generated",
        "transaction": "lazy_listing",
        "spans": ["image_sanitize", "gemma_identify", "tabpfn_price", "gemma_listing_text", "db_write"],
        "sentry_configured": bool(settings.sentry_dsn),
        "attributes": {
            "cost": "0 for local; hosted per Google AI Studio free tier/quota",
            "storage_backend": get_storage_backend(),
        }
    }
