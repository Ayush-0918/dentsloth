"""Atlas Vector Search & in-memory cosine matching engine for DentSloth."""
import logging
from typing import List, Dict, Any, Tuple
from ..db import get_collection, get_storage_backend

logger = logging.getLogger(__name__)


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vector embeddings."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = sum(a * a for a in v1) ** 0.5
    n2 = sum(b * b for b in v2) ** 0.5
    if n1 == 0 or n2 == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (n1 * n2)))


def check_atlas_vector_search_ready() -> bool:
    """Check if Atlas Vector Search is functional on the listings collection."""
    if get_storage_backend() != "atlas":
        return False
    try:
        col = get_collection("listings")
        probe_vector = [0.0] * 64
        probe_vector[0] = 1.0
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "listing_embedding_index",
                    "path": "embedding",
                    "queryVector": probe_vector,
                    "numCandidates": 1,
                    "limit": 1,
                }
            }
        ]
        list(col.aggregate(pipeline))
        return True
    except Exception:
        return False


def search_listings_by_vector(
    query_vector: list[float],
    limit: int = 10,
    min_score: float = 0.35,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Search published listings using Atlas Vector Search if ready,
    falling back to in-memory cosine similarity matching.
    Returns: (matching_listings, active_matching_mode)
    """
    col = get_collection("listings")

    # 1. Attempt Atlas Vector Search
    if get_storage_backend() == "atlas":
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "listing_embedding_index",
                        "path": "embedding",
                        "queryVector": query_vector,
                        "numCandidates": max(limit * 5, 20),
                        "limit": limit,
                    }
                },
                {"$match": {"status": "published"}}
            ]
            results = list(col.aggregate(pipeline))
            if results:
                return results, "atlas"
        except Exception as e:
            logger.debug(f"Atlas Vector Search unavailable ({e}); falling back to cosine.")

    # 2. In-memory cosine similarity fallback
    listings = list(col.find({"status": "published"}))
    scored = []
    for item in listings:
        emb = item.get("embedding", [])
        score = cosine_similarity(query_vector, emb)
        if score >= min_score or not emb:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]], "in_memory_cosine"
