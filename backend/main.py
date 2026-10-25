"""DentSloth FastAPI application entry-point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .db import ping_db
from .api import identify

logging.basicConfig(level=get_settings().log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    logger.info(f"DentSloth starting | env={settings.app_env} demo_mode={settings.is_demo}")
    if ping_db():
        logger.info("DB ping OK")
    else:
        logger.warning("DB not reachable – starting in degraded mode (OK for demo)")
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
async def health():
    """Health check endpoint."""
    db_ok = ping_db()
    return {
        "status": "ok",
        "demo_mode": settings.is_demo,
        "db": "ok" if db_ok else "degraded",
        "llm_provider": settings.llm_provider,
    }


# Register routers
app.include_router(identify.router, prefix="/api")
# Routers to be wired in subsequent phases:
# from .api import price, listings, wishlist, kit
# app.include_router(price.router, prefix="/api")
# app.include_router(listings.router, prefix="/api")
# app.include_router(wishlist.router, prefix="/api")
# app.include_router(kit.router, prefix="/api")
