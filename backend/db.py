"""MongoDB connection with seamless local SQLite fallback for offline execution."""
import json
import logging
import os
import sqlite3
import uuid
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from .config import get_settings

logger = logging.getLogger(__name__)

_mongo_client: Optional[MongoClient] = None
_use_fallback: Optional[bool] = None

SQLITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "dentsloth_local.db",
)


class LocalDocResult:
    def __init__(self, inserted_id: str):
        self.inserted_id = inserted_id


class LocalCursor:
    def __init__(self, items: list[dict]):
        self._items = items
        self._pos = 0

    def sort(self, key_or_list, direction=None):
        # basic sort support
        field = key_or_list if isinstance(key_or_list, str) else key_or_list[0][0]
        reverse = direction == -1 if direction else (key_or_list[0][1] == -1 if isinstance(key_or_list, list) else False)
        self._items.sort(key=lambda x: str(x.get(field, "")), reverse=reverse)
        return self

    def limit(self, n: int):
        self._items = self._items[:n]
        return self

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)


class LocalCollection:
    """Thread-safe SQLite-backed collection implementing MongoDB collection interface."""

    def __init__(self, collection_name: str, db_path: str = SQLITE_PATH):
        self.name = collection_name
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_table()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_table(self):
        with self._get_conn() as conn:
            conn.execute(
                f"""CREATE TABLE IF NOT EXISTS {self.name} (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            conn.commit()

    def insert_one(self, doc: dict) -> LocalDocResult:
        doc_copy = dict(doc)
        doc_id = str(doc_copy.get("_id") or uuid.uuid4().hex)
        doc_copy["_id"] = doc_id

        # Serialize datetimes or custom objects
        clean_json = json.dumps(doc_copy, default=str)
        with self._get_conn() as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {self.name} (id, data) VALUES (?, ?)",
                (doc_id, clean_json),
            )
            conn.commit()
        return LocalDocResult(inserted_id=doc_id)

    def find_one(self, filter_dict: Optional[dict] = None) -> Optional[dict]:
        items = list(self.find(filter_dict))
        return items[0] if items else None

    def find(self, filter_dict: Optional[dict] = None) -> LocalCursor:
        filter_dict = filter_dict or {}
        with self._get_conn() as conn:
            cursor = conn.execute(f"SELECT data FROM {self.name}")
            rows = cursor.fetchall()

        matched = []
        for r in rows:
            try:
                item = json.loads(r["data"])
            except Exception:
                continue

            # In-memory filter matching
            matches = True
            for k, v in filter_dict.items():
                if k == "_id":
                    if str(item.get("_id")) != str(v):
                        matches = False
                        break
                elif k.startswith("$") or isinstance(v, dict):
                    # pass through or handle basic comparison
                    pass
                elif item.get(k) != v:
                    matches = False
                    break
            if matches:
                matched.append(item)

        return LocalCursor(matched)

    def update_one(self, filter_dict: dict, update_dict: dict) -> bool:
        target = self.find_one(filter_dict)
        if not target:
            return False

        if "$set" in update_dict:
            for k, v in update_dict["$set"].items():
                target[k] = v
        if "$addToSet" in update_dict:
            for k, v in update_dict["$addToSet"].items():
                lst = target.get(k, [])
                if v not in lst:
                    lst.append(v)
                target[k] = lst

        clean_json = json.dumps(target, default=str)
        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE {self.name} SET data = ? WHERE id = ?",
                (clean_json, target["_id"]),
            )
            conn.commit()
        return True

    def count_documents(self, filter_dict: Optional[dict] = None) -> int:
        return len(list(self.find(filter_dict)))

    def delete_one(self, filter_dict: dict) -> bool:
        target = self.find_one(filter_dict)
        if not target:
            return False
        with self._get_conn() as conn:
            conn.execute(f"DELETE FROM {self.name} WHERE id = ?", (target["_id"],))
            conn.commit()
        return True


def get_client() -> Optional[MongoClient]:
    global _mongo_client
    if _mongo_client is None:
        settings = get_settings()
        try:
            _mongo_client = MongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
            )
        except Exception as e:
            logger.warning(f"Could not initialize MongoClient: {e}")
    return _mongo_client


def ping_db() -> bool:
    """Check MongoDB reachability."""
    global _use_fallback
    try:
        client = get_client()
        if client:
            client[get_settings().mongodb_db].command("ping")
            _use_fallback = False
            return True
    except Exception:
        pass
    _use_fallback = True
    return False


def get_collection(name: str):
    """Returns MongoDB collection if connected, else returns LocalCollection."""
    global _use_fallback
    if _use_fallback is None:
        ping_db()

    if not _use_fallback:
        try:
            return get_client()[get_settings().mongodb_db][name]
        except Exception:
            _use_fallback = True

    return LocalCollection(name)
