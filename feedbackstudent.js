/**
 * feedback.js
 * Handles the student feedback submission form and list rendering.
 * Used by: feedback_student.html
 * Backend: replace BASE_URL with your Flask/Node server origin.
 */

const BASE_URL = '';  // e.g. 'http://localhost:5000'

// ── Mock data ─────────────────────────────────────────────────────────────────

const MOCK_SESSIONS = [
  { id: 1, subject: 'Algebra Support',  tutor: 'Dr. Smith',  date: '2025-04-20' },
  { id: 2, subject: 'Essay Writing',    tutor: 'Ms. Patel',  date: '2025-04-22' },
  { id: 3, subject: 'Physics Revision', tutor: 'Mr. Nguyen', date: '2025-04-25' },
];

const MOCK_MY_FEEDBACK = [
  { id: 1, session: 'Algebra Support',  rating: 5, comment: 'Dr. Smith explained everything clearly!', date: '2025-04-21' },
  { id: 2, session: 'Essay Writing',    rating: 4, comment: 'Really helpful structure advice.',         date: '2025-04-23' },
];

// ── API helpers ───────────────────────────────────────────────────────────────

async function apiFetch(endpoint) {
  const res = await fetch(`${BASE_URL}${endpoint}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function apiPost(endpoint, body) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ── Star rating widget ────────────────────────────────────────────────────────

function initStarRating() {
  const stars = document.querySelectorAll('.star-btn');
  const input = document.getElementById('fbRating');
  if (!stars.length) return;

  function highlight(n) {
    stars.forEach((s, i) => s.classList.toggle('active', i < n));
  }

  stars.forEach(btn => {
    btn.addEventListener('mouseenter', () => highlight(+btn.dataset.value));
    btn.addEventListener('mouseleave', () => highlight(+input.value));
    btn.addEventListener('click', () => {
      input.value = btn.dataset.value;
      highlight(+btn.dataset.value);
    });
  });
}

// ── Render helpers ────────────────────────────────────────────────────────────

function starsHtml(rating) {
  return '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
}

function showAlert(message, type = 'success') {
  const el = document.getElementById('formAlert');
  el.textContent = message;
  el.className = `alert alert-${type}`;
  el.classList.remove('d-none');
  setTimeout(() => el.classList.add('d-none'), 4000);
}

function populateSessionDropdown(sessions) {
  const select = document.getElementById('fbSession');
  if (!select) return;
  sessions.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = `${s.subject} — ${s.tutor} (${s.date})`;
    select.appendChild(opt);
  });
}

function renderMyFeedback(list) {
  const el = document.getElementById('myFeedbackList');
  if (!el) return;
  if (!list.length) {
    el.innerHTML = '<p class="text-muted">You haven\'t submitted any feedback yet.</p>';
    return;
  }
  el.innerHTML = list.map(f => `
    <div class="feedback-card card mb-3">
      <div class="card-body">
        <div class="d-flex justify-content-between mb-1">
          <h6 class="m-0">${f.session}</h6>
          <span class="text-muted" style="font-size:0.82rem">${f.date}</span>
        </div>
        <div style="color:#f0a500;font-size:1.1rem;margin-bottom:6px">${starsHtml(f.rating)}</div>
        <div class="note-box">${f.comment}</div>
      </div>
    </div>
  `).join('');
}

// ── Form submission ───────────────────────────────────────────────────────────

async function handleSubmit(myFeedbackCache) {
  const sessionId = document.getElementById('fbSession').value;
  const rating    = +document.getElementById('fbRating').value;
  const comment   = document.getElementById('fbComment').value.trim();

  if (!sessionId) { showAlert('Please select a session.', 'warning'); return; }
  if (!rating)    { showAlert('Please choose a rating.', 'warning');  return; }
  if (!comment)   { showAlert('Please write a comment.', 'warning');  return; }

  const payload = { session_id: sessionId, rating, comment };

  let newEntry;
  try {
    newEntry = await apiPost('/api/feedback', payload);
  } catch {
    // Mock response while backend unavailable
    const sessionEl = document.getElementById('fbSession');
    newEntry = {
      id: Date.now(),
      session: sessionEl.options[sessionEl.selectedIndex].text.split(' — ')[0],
      rating,
      comment,
      date: new Date().toISOString().slice(0, 10),
    };
  }

  // Prepend to local cache and re-render
  myFeedbackCache.unshift(newEntry);
  renderMyFeedback(myFeedbackCache);

  // Reset form
  document.getElementById('fbSession').value = '';
  document.getElementById('fbRating').value = '0';
  document.getElementById('fbComment').value = '';
  document.querySelectorAll('.star-btn').forEach(s => s.classList.remove('active'));

  showAlert('Feedback submitted! Thank you.', 'success');
}

// ── Layout + init ─────────────────────────────────────────────────────────────

async function loadFeedbackPage() {
  // Init star rating
  initStarRating();

  // Load sessions for dropdown
  let sessions, myFeedback;
  try {
    [sessions, myFeedback] = await Promise.all([
      apiFetch('/api/sessions/completed'),  // sessions eligible for feedback
      apiFetch('/api/feedback/mine'),
    ]);
  } catch {
    sessions   = MOCK_SESSIONS;
    myFeedback = MOCK_MY_FEEDBACK;
  }

  populateSessionDropdown(sessions);
  renderMyFeedback(myFeedback);

  // Wire up submit button
  const submitBtn = document.getElementById('submitFeedbackBtn');
  if (submitBtn) {
    submitBtn.addEventListener('click', () => handleSubmit(myFeedback));
  }
}

document.addEventListener('DOMContentLoaded', loadFeedbackPage);
