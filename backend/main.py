"""
Ivory Dental Clinic — FastAPI Backend
Run: uvicorn main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import connect_db, close_db
from routers import webhook, conversations, appointments
from clinic_data import AGENT_SYSTEM_PROMPT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Ivory Dental Clinic API",
    description="Backend for the ElevenLabs voice agent demo.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dental-appointment-booking-agent.vercel.app/"],      # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(webhook.router,       prefix="/api/webhook",       tags=["Webhook"])
app.include_router(conversations.router, prefix="/api/conversations",  tags=["Conversations"])
app.include_router(appointments.router,  prefix="/api/appointments",   tags=["Appointments"])


# ─── Root ─────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Ivory Dental Clinic API",
        "status":  "running",
        "docs":    "/docs",
    }


@app.get("/api/agent-prompt", tags=["Agent"])
async def get_agent_prompt():
    """Returns the recommended ElevenLabs agent system prompt."""
    return {"system_prompt": AGENT_SYSTEM_PROMPT}
