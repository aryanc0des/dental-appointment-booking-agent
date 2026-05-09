/**
 * Ivory Dental Clinic — Frontend App
 *
 * Polls the FastAPI backend for:
 *  - Latest conversation transcript  (/api/conversations/latest)
 *  - Latest appointment              (/api/appointments/latest)
 *  - Full conversation history       (/api/conversations)
 *  - Full appointment history        (/api/appointments)
 *
 * Change API_BASE if your backend is on a different host/port.
 */

const API_BASE = "https://dental-appointment-booking-agent.onrender.com";

// ─── State ────────────────────────────────────────────────────────────────────
let lastConvId    = null;
let lastApptId    = null;
let activeTab     = "conversations";
let isRefreshing  = false;

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const transcriptArea  = document.getElementById("transcript-area");
const bookingArea     = document.getElementById("booking-area");
const convTbody       = document.getElementById("conv-tbody");
const apptTbody       = document.getElementById("appt-tbody");
const refreshDot      = document.getElementById("refresh-dot");
const refreshLabel    = document.getElementById("refresh-label");

// ─── Tab switching ────────────────────────────────────────────────────────────
window.switchTab = function (tab, btn) {
  activeTab = tab;

  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  document.getElementById("tab-conversations").style.display = tab === "conversations" ? "block" : "none";
  document.getElementById("tab-appointments").style.display  = tab === "appointments"  ? "block" : "none";
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmtDate(iso) {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short", day: "numeric", year: "numeric",
      hour: "numeric", minute: "2-digit"
    }).format(new Date(iso));
  } catch { return iso; }
}

function truncate(str, len = 80) {
  if (!str) return "—";
  return str.length > len ? str.slice(0, len) + "…" : str;
}

function statusBadge(status) {
  const map = {
    success:    ["badge-success",    "Success"],
    failed:     ["badge-failed",     "Failed"],
    incomplete: ["badge-incomplete", "Incomplete"],
    confirmed:  ["badge-confirmed",  "Confirmed"],
    rejected:   ["badge-rejected",   "Rejected"],
  };
  const [cls, label] = map[status] || ["badge-incomplete", status];
  return `<span class="badge ${cls}">${label}</span>`;
}

async function apiFetch(path) {
  const r = await fetch(API_BASE + path);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

function setRefreshing(on) {
  isRefreshing = on;
  refreshDot.classList.toggle("spinning", on);
}

// ─── Transcript rendering ─────────────────────────────────────────────────────
function renderTranscript(conv) {
  if (!conv || !conv.transcript) {
    transcriptArea.innerHTML = `
      <div class="transcript-empty">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
        </svg>
        <p>No conversation yet.<br>Start speaking to the assistant above.</p>
      </div>`;
    return;
  }

  const lines = conv.transcript.split("\n").filter(l => l.trim());
  const bubbles = lines.map(line => {
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) return "";
    const role = line.slice(0, colonIdx).trim().toLowerCase();
    const msg  = line.slice(colonIdx + 1).trim();
    const isAgent = role === "agent";
    const initials = isAgent ? "AI" : "You";

    return `
      <div class="msg-row ${isAgent ? "agent" : "user"}">
        <div class="msg-avatar">${initials}</div>
        <div class="msg-bubble">${escapeHtml(msg)}</div>
      </div>`;
  }).join("");

  transcriptArea.innerHTML = `<div class="transcript-scroll">${bubbles}</div>`;

  // Scroll to bottom
  const scroll = transcriptArea.querySelector(".transcript-scroll");
  if (scroll) scroll.scrollTop = scroll.scrollHeight;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ─── Booking status rendering ─────────────────────────────────────────────────
function renderBooking(conv, appt) {
  // Use most recent appointment if available
  if (appt) {
    const timeStr  = fmtDate(appt.appointment_time);
    const statusEl = statusBadge(appt.status);

    bookingArea.innerHTML = `
      <div class="booking-result ${appt.status === "confirmed" ? "success" : "failed"}">
        <div class="booking-result-badge">
          ${appt.status === "confirmed" ? "✓ Confirmed" : "✗ Rejected"}
        </div>
        <div class="booking-field">
          <span class="booking-field-label">Patient</span>
          <span class="booking-field-value">${escapeHtml(appt.patient_name)}</span>
        </div>
        <div class="booking-field">
          <span class="booking-field-label">Service</span>
          <span class="booking-field-value">${escapeHtml(appt.service_type)}</span>
        </div>
        <div class="booking-field">
          <span class="booking-field-label">Appointment Time</span>
          <span class="booking-field-value">${timeStr}</span>
        </div>
        <div class="booking-field">
          <span class="booking-field-label">Status</span>
          <span class="booking-field-value">${statusEl}</span>
        </div>
      </div>`;
    return;
  }

  // Fall back to booking_status from conversation
  if (conv && conv.booking_status) {
    const statusMap = {
      success:    { cls: "success",    icon: "✓", label: "Booking Successful" },
      failed:     { cls: "failed",     icon: "✗", label: "Booking Failed" },
      incomplete: { cls: "incomplete", icon: "◌", label: "Booking Incomplete" },
    };
    const { cls, icon, label } = statusMap[conv.booking_status] || statusMap.incomplete;

    bookingArea.innerHTML = `
      <div class="booking-result ${cls}">
        <div class="booking-result-badge">${icon} ${label}</div>
        <div class="booking-field">
          <span class="booking-field-label">Conversation ID</span>
          <span class="booking-field-value" style="font-size:0.78rem;word-break:break-all">${conv.caller_id}</span>
        </div>
      </div>`;
    return;
  }

  bookingArea.innerHTML = `
    <div class="booking-idle">
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/>
        <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
      </svg>
      <p>Booking result will appear<br>after the conversation ends.</p>
    </div>`;
}

// ─── History tables ───────────────────────────────────────────────────────────
function renderConvTable(convs) {
  if (!convs || convs.length === 0) {
    convTbody.innerHTML = `
      <tr><td colspan="4">
        <div class="empty-state">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
          </svg>
          <p>No conversations stored yet.</p>
        </div>
      </td></tr>`;
    return;
  }

  convTbody.innerHTML = convs.map(c => `
    <tr>
      <td style="font-size:0.75rem;word-break:break-all;max-width:160px;color:var(--text-mid)">${c.caller_id}</td>
      <td>${statusBadge(c.booking_status)}</td>
      <td class="td-transcript">${escapeHtml(truncate(c.transcript))}</td>
      <td class="td-date">${fmtDate(c.created_at)}</td>
    </tr>`).join("");
}

function renderApptTable(appts) {
  if (!appts || appts.length === 0) {
    apptTbody.innerHTML = `
      <tr><td colspan="4">
        <div class="empty-state">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <p>No appointments stored yet.</p>
        </div>
      </td></tr>`;
    return;
  }

  apptTbody.innerHTML = appts.map(a => `
    <tr>
      <td style="font-weight:500">${escapeHtml(a.patient_name)}</td>
      <td>${escapeHtml(a.service_type)}</td>
      <td class="td-date">${fmtDate(a.appointment_time)}</td>
      <td>${statusBadge(a.status)}</td>
    </tr>`).join("");
}

// ─── Main poll cycle ──────────────────────────────────────────────────────────
async function refresh() {
  if (isRefreshing) return;
  setRefreshing(true);

  try {
    const [conv, appt, convs, appts] = await Promise.all([
      apiFetch("/api/conversations/latest").catch(() => null),
      apiFetch("/api/appointments/latest").catch(() => null),
      apiFetch("/api/conversations?limit=20").catch(() => []),
      apiFetch("/api/appointments?limit=20").catch(() => []),
    ]);

    renderTranscript(conv);
    renderBooking(conv, appt);
    renderConvTable(convs);
    renderApptTable(appts);

    refreshLabel.textContent = `Last updated ${new Date().toLocaleTimeString()}`;
    lastConvId = conv?._id ?? lastConvId;
    lastApptId = appt?._id ?? lastApptId;

  } catch (err) {
    console.error("Refresh error:", err);
    refreshLabel.textContent = "Backend unreachable — retrying…";
  } finally {
    setRefreshing(false);
  }
}

// ─── Boot ─────────────────────────────────────────────────────────────────────
refresh();
setInterval(refresh, 6000);   // Poll every 6 seconds
