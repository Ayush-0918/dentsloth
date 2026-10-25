#!/usr/bin/env python3
"""
Create Atlas Vector Search index on MongoDB Atlas for DentSloth listings.

Usage:
    python scripts/create_vector_index.py

Manual UI Steps (MongoDB Atlas):
1. Log in to cloud.mongodb.com and navigate to your Database Deployment.
2. Click the "Atlas Search" / "Search and Vector Search" tab.
3. Click "Create Search Index" and choose the "JSON Editor" option.
4. Select Database "dentsloth" and Collection "listings".
5. Name the index "listing_embedding_index".
6. Paste the contents of scripts/atlas_index.json:
   {
     "fields": [
       {
         "type": "vector",
         "path": "embedding",
         "numDimensions": 64,
         "similarity": "cosine"
       }
     ]
   }
7. Click "Next" -> "Create Search Index". Index build takes 1-3 minutes.
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv

load_dotenv()

from backend.config import get_settings
from backend.db import get_client, ping_db, get_storage_backend


def create_vector_index():
    print("=" * 70)
    print(" 🔍 MongoDB Atlas Vector Search Index Initializer")
    print("=" * 70)

    if not ping_db():
        print("❌ Cannot connect to MongoDB Atlas.")
        print("   Please check your MONGODB_URI in .env or Render dashboard.")
        print("   DentSloth will seamlessly use in-memory cosine fallback.")
        return

    client = get_client()
    settings = get_settings()
    db = client[settings.mongodb_db]
    collection = db["listings"]

    index_def = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 64,
                "similarity": "cosine",
            }
        ]
    }

    print(f"Connecting to database '{settings.mongodb_db}', collection 'listings'...")

    try:
        from pymongo.operations import SearchIndexModel
        model = SearchIndexModel(
            definition=index_def,
            name="listing_embedding_index",
            type="vectorSearch",
        )
        result = collection.create_search_index(model=model)
        print(f"✅ Atlas Vector Search index creation requested successfully: {result}")
        print("   Status: Index is building in Atlas (~1-3 minutes).")
    except Exception as err:
        print(f"ℹ️  Automated API index creation returned: {err}")
        print("\n📋 EXACT ATLAS UI STEPS TO COMPLETE MANUALLY:")
        print("1. Go to cloud.mongodb.com -> Database Deployments -> Atlas Search.")
        print("2. Click 'Create Search Index' -> 'JSON Editor'.")
        print(f"3. Select Database: '{settings.mongodb_db}' | Collection: 'listings'.")
        print("4. Index Name: 'listing_embedding_index'.")
        print("5. Configuration JSON:\n" + json.dumps(index_def, indent=2))
        print("6. Click 'Create Search Index'.")
        print("   DentSloth will automatically detect it once status becomes 'READY'.")


if __name__ == "__main__":
    create_vector_index()
