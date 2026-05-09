# 🦷 Ivory Dental Clinic — AI Voice Assistant

A full-stack demo dental clinic system powered by an **ElevenLabs Conversational AI agent**, **FastAPI** backend, and **MongoDB** storage.

---

## System Architecture

```
Browser (Frontend)
    │
    │  voice via microphone
    ▼
ElevenLabs Agent  ──── server tool call ────►  POST /api/appointments/book
    │                                                    │
    │  post-call webhook                                 │ saves appointment to MongoDB
    ▼                                                    ▼
POST /api/webhook/elevenlabs                        MongoDB
    │                                               ┌──────────────┐
    │ saves transcript + booking status             │ conversations│
    ▼                                               │ appointments │
MongoDB                                             └──────────────┘
    ▲
    │  GET /api/conversations
    │  GET /api/appointments
    │
Frontend (polls every 6 s)
```

---

## Project Structure

```
dental-clinic/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings from .env
│   ├── database.py          # MongoDB (Motor async) connection
│   ├── models.py            # Pydantic request/response models
│   ├── clinic_data.py       # Demo clinic info + agent system prompt
│   ├── requirements.txt
│   └── routers/
│       ├── webhook.py       # POST /api/webhook/elevenlabs
│       ├── appointments.py  # POST /api/appointments/book  GET /api/appointments
│       └── conversations.py # GET /api/conversations  GET /api/conversations/latest
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js               # Polling + rendering logic
├── .env.example
└── README.md
```

---

## Quick Start

### 1. MongoDB

Make sure MongoDB is running locally:
```bash
mongod --dbpath /your/data/path
```
Or use MongoDB Atlas (free tier). The backend auto-creates collections and indexes on startup.

---

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example .env
# → fill in your values (see Environment Variables section below)

uvicorn main:app --reload --port 8000
```

Visit **http://localhost:8000/docs** to see the interactive API docs.

---

### 3. Expose Backend to the Internet (for ElevenLabs webhooks)

ElevenLabs needs to reach your backend. Use **ngrok** during development:

```bash
ngrok http 8000
# → copy the https URL, e.g. https://abc123.ngrok.io
```

Set `BACKEND_URL=https://abc123.ngrok.io` in your `.env`.

---

### 4. ElevenLabs Setup

#### 4.1 Create an Account
Go to [elevenlabs.io](https://elevenlabs.io) → sign up → open **Conversational AI** in the sidebar.

#### 4.2 Create a New Agent
- Click **"Create Agent"** → choose **"Blank template"**
- **Name**: `Ivory Dental Assistant`

#### 4.3 Configure the System Prompt
Copy the exact prompt from your backend:
```bash
curl http://localhost:8000/api/agent-prompt
```
Paste the returned `system_prompt` into the **"System Prompt"** field in ElevenLabs.

#### 4.4 Choose a Voice
- Recommended: **"Rachel"** or **"Domi"** (professional, clear)
- Set **Language** to `English`

#### 4.5 Add the Booking Tool (Server Tool)
This is how the agent books appointments during the conversation.

1. In your agent settings, go to **"Tools"** → **"Add Tool"**
2. Choose **"Webhook"** (server-side tool)
3. Fill in:

| Field         | Value                                            |
|---------------|--------------------------------------------------|
| Name          | `book_appointment`                               |
| Description   | `Books a dental appointment for the patient. Call this when the patient confirms their name, service, and preferred time.` |
| Method        | `POST`                                           |
| URL           | `https://YOUR_NGROK_URL/api/appointments/book`   |

4. Add these **parameters** (the agent will collect these from the conversation):

| Parameter          | Type   | Description                                              | Required |
|--------------------|--------|----------------------------------------------------------|----------|
| `patient_name`     | string | Full name of the patient                                 | ✅       |
| `service_type`     | string | Service requested (e.g. "Teeth Cleaning")                | ✅       |
| `appointment_time` | string | Requested date and time (e.g. "Monday at 10 AM")        | ✅       |
| `conversation_id`  | string | ElevenLabs conversation ID (passed automatically)        | ❌       |

5. Click **Save**.

#### 4.6 Configure Post-Call Webhook
This fires after every conversation ends and saves the transcript to MongoDB.

1. In your agent settings → **"Webhooks"** → **"Post-call webhook"**
2. Set URL to: `https://YOUR_NGROK_URL/api/webhook/elevenlabs`
3. (Optional) Copy the **Signing Secret** → paste into `ELEVENLABS_WEBHOOK_SECRET` in `.env`
4. Click **Save**.

#### 4.7 Get Your Agent ID
- In the agent settings, find the **Agent ID** (looks like `agent_xxxxxxxxxxxxxxxx`)
- Copy it

---

### 5. Frontend

1. Open `frontend/index.html` in a text editor
2. Find this line:
   ```html
   <elevenlabs-convai agent-id="YOUR_AGENT_ID"></elevenlabs-convai>
   ```
3. Replace `YOUR_AGENT_ID` with your actual agent ID

4. Open `frontend/index.html` directly in a browser  
   *(or serve it with a simple HTTP server)*:
   ```bash
   cd frontend
   python -m http.server 3000
   # → open http://localhost:3000
   ```

---

## Environment Variables

Copy `.env.example` to `.env` in the `backend/` folder:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=dental_clinic

ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_AGENT_ID=your_agent_id_here
ELEVENLABS_WEBHOOK_SECRET=your_webhook_secret_here

BACKEND_URL=https://your-ngrok-url.ngrok.io
```

---

## Demo Clinic Data

The system uses the following demo data (defined in `backend/clinic_data.py`):

**Ivory Dental Clinic**  
📍 14 Whitmore Street, Midtown, NY 10001  
📞 +1 (212) 555-0192

| Service              | Price  | Duration |
|----------------------|--------|----------|
| General Checkup      | $80    | 30 min   |
| Teeth Cleaning       | $120   | 45 min   |
| Teeth Whitening      | $250   | 60 min   |
| Dental X-Ray         | $60    | 20 min   |
| Root Canal           | $800   | 90 min   |
| Dental Crown         | $1,200 | 120 min  |
| Tooth Extraction     | $200   | 45 min   |
| Braces Consultation  | $150   | 45 min   |

**Slot availability:**
- Mon–Fri: 9 AM, 10 AM, 11 AM, 2 PM, 3 PM, 4 PM
- Saturday: 9 AM, 10 AM, 11 AM
- Sunday: Closed

---

## API Reference

| Method | Path                           | Description                                  |
|--------|--------------------------------|----------------------------------------------|
| POST   | `/api/webhook/elevenlabs`      | ElevenLabs post-call webhook receiver        |
| POST   | `/api/appointments/book`       | Book an appointment (called by agent tool)   |
| GET    | `/api/appointments/`           | List all appointments                        |
| GET    | `/api/appointments/latest`     | Most recent appointment                      |
| GET    | `/api/conversations/`          | List all conversations                       |
| GET    | `/api/conversations/latest`    | Most recent conversation                     |
| GET    | `/api/agent-prompt`            | Returns the agent system prompt text         |
| GET    | `/docs`                        | Swagger UI (interactive API docs)            |

---

## MongoDB Collections

### `conversations`
```json
{
  "_id": "ObjectId",
  "caller_id": "conv_abc123",
  "transcript": "User: I'd like to book...\nAgent: Of course! ...",
  "booking_status": "success | failed | incomplete",
  "created_at": "2025-03-10T14:30:00Z",
  "duration_secs": 45,
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

## How the Flow Works

1. User opens the frontend and clicks the ElevenLabs microphone widget
2. User speaks: *"Hi, I'd like to book a teeth cleaning for Monday at 10 AM"*
3. Agent collects: name, service, time
4. Agent calls the `book_appointment` tool → hits `POST /api/appointments/book`
5. Backend validates the slot, saves to MongoDB `appointments`, returns confirmation text
6. Agent reads the confirmation aloud to the patient
7. Conversation ends → ElevenLabs fires post-call webhook → `POST /api/webhook/elevenlabs`
8. Backend saves full transcript + booking status to MongoDB `conversations`
9. Frontend polls every 6 seconds → displays transcript, booking card, and history tables

---

## Tech Stack

| Layer    | Technology                    |
|----------|-------------------------------|
| Voice AI | ElevenLabs Conversational AI  |
| Backend  | Python 3.11+, FastAPI, Uvicorn|
| Database | MongoDB, Motor (async driver) |
| Frontend | HTML, CSS, Vanilla JavaScript |
