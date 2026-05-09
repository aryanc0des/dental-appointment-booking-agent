"""
Appointments Router
─────────────────────────────────────────────────────────────────────────────
POST /api/appointments/book   ← called by ElevenLabs agent as a server tool
GET  /api/appointments        ← frontend polling
GET  /api/appointments/latest ← frontend live status
"""

import logging
from datetime import datetime, timezone

import dateparser
from fastapi import APIRouter

from clinic_data import OPEN_DAYS, SATURDAY_SLOTS, SERVICE_NAMES, WEEKDAY_SLOTS
from database import get_db
from models import BookAppointmentRequest

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_time(raw: str) -> datetime | None:
    dp_settings = {"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": False}
    return dateparser.parse(raw, settings=dp_settings)


def _validate_slot(dt: datetime) -> str | None:
    day_name = dt.strftime("%A").lower()
    if day_name not in OPEN_DAYS:
        return f"We are closed on {dt.strftime('%A')}. We're open Monday through Saturday."
    slot_str = dt.strftime("%H:%M")
    allowed = SATURDAY_SLOTS if day_name == "saturday" else WEEKDAY_SLOTS
    if slot_str not in allowed:
        readable = ", ".join(
            datetime.strptime(s, "%H:%M").strftime("%I:%M %p").lstrip("0") for s in allowed
        )
        return (
            f"Sorry, {slot_str} isn't an available slot on {dt.strftime('%A')}. "
            f"Available times are: {readable}."
        )
    return None


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/book")
async def book_appointment(req: BookAppointmentRequest):
    """Called by ElevenLabs agent as a server-side tool during a conversation."""
    db = get_db()

    dt = _parse_time(req.appointment_time)
    if not dt:
        return {
            "result": (
                "I couldn't understand that date and time. "
                "Could you say it again? For example: 'Monday at 10 AM'."
            )
        }

    slot_error = _validate_slot(dt)
    if slot_error:
        return {"result": slot_error}

    # Use a 1-hour window instead of exact equality.
    # dateparser can produce slightly different datetime objects for the
    # same spoken slot (microseconds, tz offsets), so exact == is unreliable.
    window_start = dt.replace(minute=0, second=0, microsecond=0)
    window_end   = dt.replace(minute=59, second=59, microsecond=999999)
    existing = await db.appointments.find_one({
        "appointment_time": {"$gte": window_start, "$lte": window_end},
        "status": "confirmed",
    })
    if existing:
        return {
            "result": (
                f"Unfortunately the {dt.strftime('%I:%M %p').lstrip('0')} slot on "
                f"{dt.strftime('%A, %B %d')} is already taken. "
                "Would you like a different time?"
            )
        }

    matched_service = next(
        (s for s in SERVICE_NAMES if s.lower() in req.service_type.lower()),
        req.service_type,
    )

    doc = {
        "patient_name": req.patient_name.strip().title(),
        "service_type": matched_service,
        "appointment_time": dt,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc),
        "conversation_id": req.conversation_id,
    }

    result = await db.appointments.insert_one(doc)

    if result.inserted_id:
        friendly_time = dt.strftime("%A, %B %d at %I:%M %p")
        logger.info(f"Appointment booked: {doc['patient_name']} | {matched_service} | {friendly_time}")
        return {
            "result": (
                f"All set! Your appointment for {matched_service} is confirmed for "
                f"{friendly_time}. We look forward to seeing you, "
                f"{req.patient_name.strip().split()[0].title()}! "
                "We'll give you a reminder call the day before."
            )
        }
    else:
        return {"result": "Something went wrong while saving your appointment. Please call us directly."}


@router.get("/latest")
async def latest_appointment():
    db = get_db()
    doc = await db.appointments.find_one({}, {"_raw": 0}, sort=[("created_at", -1)])
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    for field in ("appointment_time", "created_at"):
        if isinstance(doc.get(field), datetime):
            doc[field] = doc[field].isoformat()
    return doc


@router.get("/")
async def list_appointments(limit: int = 20):
    db = get_db()
    cursor = db.appointments.find({}, {"_raw": 0}).sort("created_at", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        for field in ("appointment_time", "created_at"):
            if isinstance(doc.get(field), datetime):
                doc[field] = doc[field].isoformat()
        results.append(doc)
    return results