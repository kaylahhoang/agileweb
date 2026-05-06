/**
 * dashboard.js
 * Handles data fetching and dynamic rendering for dashboard.html.
 * Backend: replace BASE_URL with your Flask/Node server origin.
 */

const BASE_URL = '';  // e.g. 'http://localhost:5000'

// ── Mock data (remove once real endpoints are ready) ─────────────────────────
const MOCK = {
  user: { name: 'Alex', role: 'student' },  // role: 'student' | 'tutor'
  stats: { sessions: 3, messages: 5, rating: 4.6 },
  sessions: [
    { id: 1, subject: 'Algebra Support',    tutor: 'Dr. Smith',  date: '2025-05-10', time: '10:00 AM', status: 'confirmed' },
    { id: 2, subject: 'Essay Writing',      tutor: 'Ms. Patel',  date: '2025-05-12', time: '2:00 PM',  status: 'pending'   },
    { id: 3, subject: 'Physics Revision',   tutor: 'Mr. Nguyen', date: '2025-05-15', time: '11:00 AM', status: 'scheduled' },
  ],
  feedback: [
    { id: 1, session: 'Algebra Support',  student: 'Emily Chen',   rating: 5, comment: 'Great explanation of quadratic equations!',           date: '2025-04-30' },
    { id: 2, session: 'Essay Writing',    student: 'Jackson Wong',  rating: 4, comment: 'Really helpful feedback on my essay structure.',       date: '2025-04-28' },
    { id: 3, session: 'Physics Revision', student: 'Sophie Tran',   rating: 5, comment: 'Clear and patient — finally understand circuits.',     date: '2025-04-25' },
  ],
};

// ── API helpers ───────────────────────────────────────────────────────────────

async function apiFetch(endpoint) {
  const res = await fetch(`${BASE_URL}${endpoint}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ── Render helpers ────────────────────────────────────────────────────────────

function statusBadge(status) {
  return `<span class="session-badge badge-${status}">${status}</span>`;
}

function starsHtml(rating) {
  return '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
}

function renderSessions(sessions) {
  const el = document.getElementById('sessionList');
  if (!sessions.length) {
    el.innerHTML = '<p class="text-muted">No upcoming sessions.</p>';
    return;
  }
  el.innerHTML = sessions.map(s => `
    <div class="upcoming-session-card mb-2">
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <p class="upcoming-subject mb-1">${s.subject}</p>
          <p class="upcoming-meta mb-1">with ${s.tutor}</p>
          <p class="upcoming-meta">${s.date} · ${s.time}</p>
          ${statusBadge(s.status)}
        </div>
        <a href="schedule.html" class="btn btn-sm btn-light">Details</a>
      </div>
    </div>
  `).join('');
}

function renderFeedback(feedbackList) {
  const el = document.getElementById('feedbackList');
  if (!feedbackList.length) {
    el.innerHTML = '<p class="text-muted">No feedback yet.</p>';
    return;
  }
  el.innerHTML = feedbackList.map(f => `
    <div class="feedback-bubble mb-3">
      <p class="feedback-text">${f.comment}</p>
      <p class="feedback-meta">
        ${starsHtml(f.rating)} · ${f.session} · ${f.student} · ${f.date}
      </p>
    </div>
  `).join('');
}

function renderStats(stats) {
  document.getElementById('statSessions').textContent = stats.sessions;
  document.getElementById('statMessages').textContent = stats.messages;
  document.getElementById('statRating').textContent = `${stats.rating} / 5`;
}

// ── Load layout then populate ─────────────────────────────────────────────────

async function loadDashboard() {
  // Fetch data (falls back to mock on error)
  let user, stats, sessions, feedback;

  try {
    [user, stats, sessions, feedback] = await Promise.all([
      apiFetch('/api/user'),
      apiFetch('/api/dashboard/stats'),
      apiFetch('/api/sessions/upcoming'),
      apiFetch('/api/feedback/recent'),
    ]);
  } catch {
    // Use mock data while backend is unavailable
    ({ user, stats, sessions, feedback } = MOCK);
  }

  // Render
  document.getElementById('welcomeHeading').textContent = `Welcome back, ${user.name}!`;
  document.getElementById('welcomeSub').textContent =
    user.role === 'tutor'
      ? "Here's your tutoring activity at a glance."
      : "Here's what's coming up for you.";

  renderStats(stats);
  renderSessions(sessions);
  renderFeedback(feedback);
}

document.addEventListener('DOMContentLoaded', loadDashboard);