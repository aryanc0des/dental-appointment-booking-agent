from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ─── Enums ────────────────────────────────────────────────────────────────────

BookingStatus = Literal["success", "failed", "incomplete"]
AppointmentStatus = Literal["confirmed", "rejected"]


# ─── Requests ─────────────────────────────────────────────────────────────────

class BookAppointmentRequest(BaseModel):
    """Sent by ElevenLabs agent as a server tool call."""
    patient_name: str
    service_type: str
    appointment_time: str          # Natural language or ISO string from agent
    conversation_id: Optional[str] = None


# ─── DB Documents (response shapes) ───────────────────────────────────────────

class ConversationOut(BaseModel):
    id: str = Field(alias="_id")
    caller_id: str
    transcript: str
    booking_status: BookingStatus
    created_at: datetime

    class Config:
        populate_by_name = True


class AppointmentOut(BaseModel):
    id: str = Field(alias="_id")
    patient_name: str
    service_type: str
    appointment_time: datetime
    status: AppointmentStatus
    created_at: datetime

    class Config:
        populate_by_name = True
