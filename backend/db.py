"""MongoDB connection – lazy, non-blocking for startup."""
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from .config import get_settings

logger = logging.getLogger(__name__)
_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Return a MongoClient (lazy singleton, no blocking retry on startup)."""
    global _client
    if _client is None:
        settings = get_settings()
        # serverSelectionTimeoutMS is per-operation, not blocking on construction
        _client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
        )
    return _client


def get_db():
    settings = get_settings()
    return get_client()[settings.mongodb_db]


def get_collection(name: str):
    return get_db()[name]


def ping_db() -> bool:
    """Non-blocking ping. Returns False if MongoDB is not reachable."""
    try:
        get_db().command("ping")
        return True
    except Exception as e:
        logger.warning(f"DB ping failed: {e}")
        return False
