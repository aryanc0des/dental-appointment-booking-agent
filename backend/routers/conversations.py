"""
Conversations Router

GET /api/conversations/        — List stored conversations (latest first).
GET /api/conversations/latest  — Single most recent conversation.
"""

from datetime import datetime
from fastapi import APIRouter

from database import get_db

router = APIRouter()


def _serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    if "created_at" in doc and isinstance(doc["created_at"], datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    doc.pop("_raw", None)   # strip raw ElevenLabs payload from public response
    return doc


@router.get("/")
async def list_conversations(limit: int = 20):
    """Return the most recent conversations stored via webhook."""
    db = get_db()
    cursor = db.conversations.find({}, {"_raw": 0}).sort("created_at", -1).limit(limit)
    return [_serialize(doc) async for doc in cursor]


@router.get("/latest")
async def latest_conversation():
    """Return the single most recent conversation."""
    db = get_db()
    doc = await db.conversations.find_one({}, {"_raw": 0}, sort=[("created_at", -1)])
    return _serialize(doc) if doc else None
