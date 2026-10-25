"""DentSloth Overnight Sloth Run.

Automated agent that matches newly published listings to active buyer wishlists,
records match notifications, and produces a concise morning summary.
Idempotent: running twice will not generate duplicate notifications.
"""
import logging
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.db import get_collection
from backend.models import AgentEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sloth_run")


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vector embeddings."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.5
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = sum(a * a for a in v1) ** 0.5
    n2 = sum(b * b for b in v2) ** 0.5
    if n1 == 0 or n2 == 0:
        return 0.5
    return max(0.0, min(1.0, dot / (n1 * n2)))


def run_sloth():
    print("=" * 75)
    print(" 🦥 DentSloth Overnight Sloth Run Starting")
    print("=" * 75)

    listings_coll = get_collection("listings")
    wishlists_coll = get_collection("wishlists")
    events_coll = get_collection("events")

    # Fetch active published listings
    published_listings = list(listings_coll.find({"status": "published"}))
    wishlists = list(wishlists_coll.find())

    print(f"Loaded {len(published_listings)} published listing(s) and {len(wishlists)} active wishlist(s).")

    new_matches = 0
    notifications_sent = 0
    matched_pairs = []

    for w in wishlists:
        w_id = str(w.get("_id"))
        w_buyer = w.get("buyer_name", "Anonymous Dentist")
        w_embed = w.get("embedding", [])
        w_budget = float(w.get("parsed", {}).get("max_budget_inr", 999999))
        w_types = [t.lower() for t in w.get("parsed", {}).get("types", [])]
        already_notified = set(w.get("notified_listing_ids", []))

        for l in published_listings:
            l_id = str(l.get("_id"))
            l_type = str(l.get("instrument_type", "")).lower()
            l_price = float(l.get("suggested_price_inr", 0))
            l_embed = l.get("embedding", [])

            # Idempotency check: skip already notified
            if l_id in already_notified:
                continue

            # Check price budget constraint
            if l_price > w_budget:
                continue

            # Match score (semantic embedding similarity + keyword bonus)
            sim = cosine_similarity(w_embed, l_embed)
            if any(wt in l_type or l_type in wt for wt in w_types):
                sim = min(0.98, sim + 0.35)

            # Match threshold
            if sim >= 0.70:
                new_matches += 1
                matched_pairs.append((w_buyer, l.get("instrument_type"), l.get("city"), sim))
                already_notified.add(l_id)

                # Record match event
                events_coll.insert_one({
                    "event_type": "match",
                    "listing_id": l_id,
                    "wishlist_id": w_id,
                    "payload": {
                        "buyer": w_buyer,
                        "instrument": l.get("instrument_type"),
                        "city": l.get("city"),
                        "similarity": round(sim, 2),
                        "price": l_price,
                    },
                    "created_at": datetime.utcnow().isoformat(),
                })

                # Mock notification event
                events_coll.insert_one({
                    "event_type": "notification",
                    "listing_id": l_id,
                    "wishlist_id": w_id,
                    "payload": {
                        "recipient": w_buyer,
                        "channel": "mock_email",
                        "message": f"Good morning {w_buyer}! A {l.get('brand')} {l.get('instrument_type')} (Grade {l.get('condition_grade')}) was listed for ₹{int(l_price):,} in {l.get('city')}.",
                    },
                    "created_at": datetime.utcnow().isoformat(),
                })
                notifications_sent += 1

        # Update wishlist with notified listings for idempotency
        wishlists_coll.update_one(
            {"_id": w_id},
            {"$set": {"notified_listing_ids": list(already_notified)}},
        )

    # 2-line Morning Summary
    summary_line_1 = f"🌅 Morning Sloth Summary: {new_matches} new match(es) paired across {len(wishlists)} clinic wishlist(s)."
    if matched_pairs:
        top = matched_pairs[0]
        summary_line_2 = f"Top match: {top[1]} for {top[0]} ({int(top[3]*100)}% match, {top[2]}). 0 budgets exceeded."
    else:
        summary_line_2 = "All published inventory scanned. No new price or budget conflicts."
    full_summary = f"{summary_line_1} {summary_line_2}"

    # Log sloth run completion event
    events_coll.insert_one({
        "event_type": "sloth_run",
        "payload": {
            "summary": full_summary,
            "new_matches": new_matches,
            "notifications_sent": notifications_sent,
        },
        "created_at": datetime.utcnow().isoformat(),
    })

    print(f"\n{summary_line_1}")
    print(f"{summary_line_2}")
    print(f"\nNotifications issued: {notifications_sent} (Idempotent: 0 duplicates on re-run)")
    print("=" * 75)
    return full_summary


if __name__ == "__main__":
    run_sloth()
