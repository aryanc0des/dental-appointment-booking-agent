# 🦷 Ivory Dental Clinic — AI Voice Booking System

A full-stack demo dental clinic system powered by an **ElevenLabs Conversational AI agent**, **FastAPI** backend, and **MongoDB** storage. Built as part of an internship assignment.

**Live Demo:** [dental-appointment-booking-agent.vercel.app](https://dental-appointment-booking-agent.vercel.app)  
**Backend API:** [dental-appointment-booking-agent.onrender.com/docs](https://dental-appointment-booking-agent.onrender.com/docs)

---

## What It Does

- 🎙️ Users speak to an AI voice agent directly in the browser
- 🗓️ The agent collects name, service, and preferred time — then books the appointment in real time
- 📝 After the call ends, the full transcript is automatically saved to MongoDB via ElevenLabs webhook
- 📊 The frontend displays live transcripts, booking confirmations, and full history — no manual data entry anywhere

---

## System Architecture

```
Browser (Frontend on Vercel)
    │
    │  voice via microphone
    ▼
ElevenLabs Agent  ──── server tool call ────►  POST /api/appointments/book
    │                                                    │
    │  post-call webhook                                 │ saves to MongoDB
    ▼                                                    ▼
POST /api/webhook/elevenlabs                        MongoDB Atlas
    │                                               ┌──────────────────┐
    │ saves transcript + booking status             │  conversations   │
    ▼                                               │  appointments    │
MongoDB Atlas                                       └──────────────────┘
    ▲
    │  polls every 6s
    │
Frontend (Vercel)
```

---

## Project Structure

```
dental-clinic/
├── backend/
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Settings loaded from .env
│   ├── database.py           # MongoDB async connection (Motor)
│   ├── models.py             # Pydantic request/response models
│   ├── clinic_data.py        # Demo clinic info + agent system prompt
│   ├── requirements.txt
│   └── routers/
│       ├── webhook.py        # POST /api/webhook/elevenlabs
│       ├── appointments.py   # POST /api/appointments/book  |  GET /api/appointments/
│       └── conversations.py  # GET /api/conversations/  |  GET /api/conversations/latest
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js                # Polling + rendering logic
├── .env.example
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- MongoDB running locally or a MongoDB Atlas account
- An ElevenLabs account
- ngrok (to expose local backend for ElevenLabs webhooks)

---

### 1. Clone the repo

```bash
git clone https://github.com/aryanc0des/dental-appointment-booking-agent.git
cd dental-clinic
```

---

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example .env
# Fill in your values (see Environment Variables below)

uvicorn main:app --reload --port 8000
```

API docs at **http://localhost:8000/docs**

---

### 3. Expose backend with ngrok

ElevenLabs needs a public HTTPS URL to fire webhooks and call the booking tool.

```bash
ngrok http 8000
# Copy the https URL → e.g. https://abc123.ngrok.io
# Set BACKEND_URL=https://abc123.ngrok.io in .env
```

---

### 4. ElevenLabs Agent Setup

#### 4.1 Create Agent
- [elevenlabs.io](https://elevenlabs.io) → **Conversational AI** → **Create Agent** → Blank template
- Name: `Ivory Dental Assistant`

#### 4.2 System Prompt
Fetch the pre-built prompt from the backend:
```bash
curl http://localhost:8000/api/agent-prompt
```
Paste the returned `system_prompt` into the agent's **System Prompt** field.

#### 4.3 Add Booking Tool (Server Tool)
**Tools** → **Add Tool** → **Webhook**

| Field | Value |
|---|---|
| Name | `book_appointment` |
| Description | `Books a dental appointment. Call only after collecting patient name, service, and preferred date/time.` |
| Method | `POST` |
| URL | `https://YOUR_NGROK_URL/api/appointments/book` |

**Body parameters** (all set to `LLM Prompt` value type):

| Parameter | Type | Required | Description |
|---|---|---|---|
| `patient_name` | string | ✅ | Full name of the patient |
| `service_type` | string | ✅ | Service requested (e.g. "Teeth Cleaning") |
| `appointment_time` | string | ✅ | Requested date and time (e.g. "Monday at 10 AM") |
| `conversation_id` | string | ❌ | ElevenLabs conversation ID |

#### 4.4 Post-Call Webhook
**Webhooks** → **Post-call webhook**
- URL: `https://YOUR_NGROK_URL/api/webhook/elevenlabs`
- Copy the **Signing Secret** → paste into `ELEVENLABS_WEBHOOK_SECRET` in `.env`

#### 4.5 Get Agent ID
Copy the **Agent ID** from agent settings → paste into `frontend/index.html`:
```html
<elevenlabs-convai agent-id="YOUR_AGENT_ID"></elevenlabs-convai>
```

---

### 5. Frontend

```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

---

## Environment Variables

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=dental_clinic

# ElevenLabs
ELEVENLABS_API_KEY=your_api_key
ELEVENLABS_AGENT_ID=your_agent_id
ELEVENLABS_WEBHOOK_SECRET=your_webhook_secret

# Your public backend URL (ngrok for local, Render URL for production)
BACKEND_URL=https://your-ngrok-url.ngrok.io
```

---

## Deployment

| Service | Platform |
|---|---|
| Frontend | Vercel — root directory: `frontend`, no build command |
| Backend | Render — root directory: `backend`, start command: `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Database | MongoDB Atlas (free tier) |

After deploying, update the ElevenLabs tool URL and webhook URL from ngrok → your Render URL.

---

## Demo Clinic Data

**Ivory Dental Clinic** · 14 Whitmore Street, Midtown, NY 10001 · +1 (212) 555-0192

| Service | Price | Duration |
|---|---|---|
| General Checkup | $80 | 30 min |
| Teeth Cleaning | $120 | 45 min |
| Teeth Whitening | $250 | 60 min |
| Dental X-Ray | $60 | 20 min |
| Root Canal | $800 | 90 min |
| Dental Crown | $1,200 | 120 min |
| Tooth Extraction | $200 | 45 min |
| Braces Consultation | $150 | 45 min |

**Available slots:** Mon–Fri: 9 AM, 10 AM, 11 AM, 2 PM, 3 PM, 4 PM · Saturday: 9 AM, 10 AM, 11 AM · Sunday: Closed

---

## API Reference

| Method | Path | Description |
|---|---|---|
| POST | `/api/webhook/elevenlabs` | ElevenLabs post-call webhook |
| POST | `/api/appointments/book` | Book appointment (agent tool) |
| GET | `/api/appointments/` | List all appointments |
| GET | `/api/appointments/latest` | Most recent appointment |
| GET | `/api/conversations/` | List all conversations |
| GET | `/api/conversations/latest` | Most recent conversation |
| GET | `/api/agent-prompt` | Returns the agent system prompt |
| GET | `/docs` | Swagger UI |

---

## MongoDB Schema

### `conversations`
```json
{
  "_id": "ObjectId",
  "caller_id": "conv_abc123",
  "transcript": "User: I'd like to book...\nAgent: Of course!...",
  "booking_status": "success | failed | incomplete",
  "created_at": "2025-03-10T14:30:00Z",
  "duration_secs": 87,
  "agent_id": "agent_xyz"
}
```

### `appointments`
```json
{
  "_id": "ObjectId",
  "patient_name": "Jane Smith",
  "service_type": "Teeth Cleaning",
  "appointment_time": "2025-03-17T10:00:00Z",
  "status": "confirmed | rejected",
  "created_at": "2025-03-10T14:30:00Z",
  "conversation_id": "conv_abc123"
}
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Voice AI | ElevenLabs Conversational AI |
| Backend | Python 3.11 · FastAPI · Uvicorn |
| Database | MongoDB Atlas · Motor (async driver) |
| Frontend | HTML · CSS · Vanilla JavaScript |
| Hosting | Vercel (frontend) · Render (backend) |