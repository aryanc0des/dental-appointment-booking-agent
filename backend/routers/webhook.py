"""
ElevenLabs Webhook Router
POST /api/webhook/elevenlabs
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from config import settings
from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Signature Verification ───────────────────────────────────────────────────

def verify_signature(body: bytes, request_headers: dict, secret: str) -> bool:
    """
    ElevenLabs header: elevenlabs-signature
    Value format:      t=<unix_timestamp>,v0=<hmac_sha256_hex>
    Signed payload:    f"{timestamp}.{raw_body}"
    """
    sig_header = request_headers.get("elevenlabs-signature", "")
    if not sig_header:
        logger.warning("No signature header found in webhook request.")
        return False

    # Parse t=... and v0=... from the header value
    parts = dict(part.split("=", 1) for part in sig_header.split(",") if "=" in part)
    timestamp = parts.get("t", "")
    received  = parts.get("v0", "")

    if not timestamp or not received:
        logger.warning(f"Malformed signature header: {sig_header}")
        return False

    # ElevenLabs signs: "<timestamp>.<raw_body>"
    signed_payload = f"{timestamp}.{body.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, received)


# ─── Transcript Helpers ───────────────────────────────────────────────────────

def format_transcript(transcript_list: list) -> str:
    if not transcript_list:
        return ""
    lines = []
    for entry in transcript_list:
        role = entry.get("role", "unknown").capitalize()
        msg  = (entry.get("message") or "").strip()
        if msg:
            lines.append(f"{role}: {msg}")
    return "\n".join(lines)


def infer_booking_status(analysis: dict, transcript_list: list) -> str:
    if analysis:
        dc = analysis.get("data_collection_results", {})
        for key in ("booking_status", "booking_outcome"):
            field = dc.get(key, {})
            if isinstance(field, dict):
                val = field.get("value", "").lower()
                if val in ("success", "confirmed", "booked"):
                    return "success"
                if val in ("failed", "rejected", "error"):
                    return "failed"

        cs = analysis.get("call_successful", "")
        if cs in ("success", True):
            return "success"
        if cs in ("failure", "failed", False):
            return "failed"

    agent_msgs = [
        e.get("message", "").lower()
        for e in transcript_list
        if e.get("role") in ("agent", "assistant")
    ]
    combined = " ".join(agent_msgs[-4:])
    if any(w in combined for w in ("confirmed", "booked", "all set", "appointment is set", "see you")):
        return "success"
    if any(w in combined for w in ("unable to book", "couldn't book", "not available", "try again", "unfortunately")):
        return "failed"

    return "incomplete"


def extract_payload(payload: dict):
    """Handle both nested {data: {...}} and flat payload shapes."""
    data = payload.get("data") or {}
    if not data and "transcript" in payload:
        data = payload

    conversation_id = (
        data.get("conversation_id")
        or payload.get("conversation_id")
        or "unknown"
    )
    transcript_raw = data.get("transcript") or payload.get("transcript", [])

    if isinstance(transcript_raw, list):
        transcript_text = format_transcript(transcript_raw)
        transcript_list = transcript_raw
    else:
        transcript_text = str(transcript_raw)
        transcript_list = []

    analysis = data.get("analysis")  or payload.get("analysis",  {}) or {}
    metadata = data.get("metadata")  or payload.get("metadata",  {}) or {}
    agent_id = data.get("agent_id")  or payload.get("agent_id",  "")

    return conversation_id, transcript_text, transcript_list, analysis, metadata, agent_id


# ─── Route ────────────────────────────────────────────────────────────────────

@router.post("/elevenlabs")
async def elevenlabs_webhook(request: Request):
    body = await request.body()

    # Log all headers once so you can confirm the exact header name in your logs
    logger.info(f"Webhook headers: { {k: v for k, v in request.headers.items()} }")

    if settings.ELEVENLABS_WEBHOOK_SECRET:
        if not verify_signature(body, dict(request.headers), settings.ELEVENLABS_WEBHOOK_SECRET):
            logger.warning("Webhook signature mismatch – rejected.")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Malformed JSON payload")

    event_type = payload.get("type", "unknown")
    logger.info(f"Webhook received — type={event_type}")

    conv_id, transcript_text, transcript_list, analysis, metadata, agent_id = \
        extract_payload(payload)

    if transcript_text:
        await _save_conversation(
            conv_id, transcript_text, transcript_list,
            analysis, metadata, agent_id, event_type
        )
    else:
        logger.info(f"No transcript in payload — skipping save. type={event_type}")

    return {"status": "ok", "event": event_type}


async def _save_conversation(
    conversation_id, transcript_text, transcript_list,
    analysis, metadata, agent_id, event_type
):
    db = get_db()

    existing = await db.conversations.find_one({"caller_id": conversation_id})
    if existing:
        logger.info(f"Duplicate webhook for {conversation_id} — skipping.")
        return

    booking_status = infer_booking_status(analysis, transcript_list)

    doc = {
        "caller_id":      conversation_id,
        "transcript":     transcript_text,
        "booking_status": booking_status,
        "created_at":     datetime.now(timezone.utc),
        "duration_secs":  metadata.get("call_duration_secs"),
        "agent_id":       agent_id,
        "event_type":     event_type,
        "_raw":           {"analysis": analysis, "metadata": metadata},
    }

    result = await db.conversations.insert_one(doc)
    logger.info(f"Conversation saved: {result.inserted_id} | status={booking_status}")