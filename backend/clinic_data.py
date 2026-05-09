"""
Demo clinic data for Ivory Dental Clinic.
This is used both to populate the agent system prompt
and to validate bookings on the backend.
"""

CLINIC = {
    "name": "Ivory Dental Clinic",
    "address": "14 Whitmore Street, Midtown, New York, NY 10001",
    "phone": "+1 (212) 555-0192",
    "email": "hello@ivorydental.com",
    "hours": {
        "Monday":    {"open": "09:00", "close": "18:00"},
        "Tuesday":   {"open": "09:00", "close": "18:00"},
        "Wednesday": {"open": "09:00", "close": "18:00"},
        "Thursday":  {"open": "09:00", "close": "18:00"},
        "Friday":    {"open": "09:00", "close": "18:00"},
        "Saturday":  {"open": "09:00", "close": "14:00"},
        "Sunday":    None,  # Closed
    },
}

SERVICES = [
    {"name": "General Checkup",       "price": 80,   "duration_min": 30},
    {"name": "Teeth Cleaning",        "price": 120,  "duration_min": 45},
    {"name": "Teeth Whitening",       "price": 250,  "duration_min": 60},
    {"name": "Dental X-Ray",          "price": 60,   "duration_min": 20},
    {"name": "Root Canal",            "price": 800,  "duration_min": 90},
    {"name": "Dental Crown",          "price": 1200, "duration_min": 120},
    {"name": "Tooth Extraction",      "price": 200,  "duration_min": 45},
    {"name": "Braces Consultation",   "price": 150,  "duration_min": 45},
]

# Slots available per weekday (24h format)
WEEKDAY_SLOTS = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
SATURDAY_SLOTS = ["09:00", "10:00", "11:00"]

OPEN_DAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}

SERVICE_NAMES = [s["name"] for s in SERVICES]


AGENT_SYSTEM_PROMPT = f"""
You are a warm, professional dental assistant for {CLINIC['name']}.
Your job is to answer patient questions, share clinic information, and book appointments.

CLINIC DETAILS:
  Name:    {CLINIC['name']}
  Address: {CLINIC['address']}
  Phone:   {CLINIC['phone']}
  Email:   {CLINIC['email']}

HOURS:
  Monday – Friday : 9:00 AM – 6:00 PM
  Saturday        : 9:00 AM – 2:00 PM
  Sunday          : Closed

AVAILABLE APPOINTMENT SLOTS:
  Monday – Friday : 9 AM, 10 AM, 11 AM, 2 PM, 3 PM, 4 PM
  Saturday        : 9 AM, 10 AM, 11 AM

SERVICES & PRICING:
  • General Checkup        – $80   (30 min)
  • Teeth Cleaning         – $120  (45 min)
  • Teeth Whitening        – $250  (60 min)
  • Dental X-Ray           – $60   (20 min)
  • Root Canal             – $800  (90 min)
  • Dental Crown           – $1,200 (120 min)
  • Tooth Extraction       – $200  (45 min)
  • Braces Consultation    – $150  (45 min)

BOOKING INSTRUCTIONS:
When a patient wants to book:
  1. Ask for their full name.
  2. Ask which service they need (offer the list if they are unsure).
  3. Ask for their preferred date and time (must fall within open hours/slots).
  4. Call the book_appointment tool with: patient_name, service_type, appointment_time (ISO 8601).
  5. Relay the tool result back to the patient.

Keep responses concise and clear – this is a voice interface.
Be empathetic; patients may be nervous about dental visits.
Never make up information. If unsure, say you'll have the front desk follow up.
""".strip()
