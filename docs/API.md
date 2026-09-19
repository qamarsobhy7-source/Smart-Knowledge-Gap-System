# API Reference

Complete documentation of all HTTP endpoints in the **Smart Knowledge Gap System**.

**Base URL:** `https://smart-knowledge-gap-system-qqbms.faable.link`

---

## 📋 Table of Contents

- [Authentication](#-authentication)
- [Assessment](#-assessment)
- [Dashboard](#-dashboard)
- [Learning Content](#-learning-content)
- [AI & ML](#-ai--ml)
- [Reports](#-reports)
- [Utilities](#-utilities)

---

## 🔐 Authentication

### `GET /`
Homepage with signup form.

**Response:** `200 OK` — HTML page

### `POST /register`
Register a new student.

**Form fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Full name (max 120 chars) |
| `email` | string | ✅ | Valid email (unique) |
| `password` | string | ✅ | Min 6 characters |
| `age` | int | ❌ | Student age |
| `subject` | string | ❌ | Preferred subject |
| `level` | string | ❌ | Beginner / Intermediate / Advanced |
| `csrf_token` | string | ✅ | CSRF protection token |

**Response:** `302` redirect to `/assessment/<student_id>`

**Errors:**
- `400` — Missing name, invalid email, short password, duplicate email

### `GET /register`
Redirects to `/` (signup form is on homepage).

### `GET /login`
Login page.

### `POST /login`
Authenticate a student.

**Form fields:** `email`, `password`, `csrf_token`

**Response:** `302` redirect to `/dashboard/<student_id>`

### `GET|POST /logout`
Destroy the current session.

### `GET|POST /forgot-password`
Request a password reset link via email.

### `GET|POST /reset-password/<token>`
Reset password using a signed token.

---

## 📝 Assessment

### `GET /assessment/<student_id>`
Show the next question for an ongoing assessment.

**Requirements:** Authenticated as `student_id`

**Response:** `200 OK` — Question page with options A/B/C/D

### `POST /assessment/<student_id>/submit`
Submit an answer for the current question.

**Form fields:** `question_id`, `student_answer`, `csrf_token`

**Response:** `200` — Next question or end of assessment

### `GET /reassessment/<student_id>`
Start a reassessment session for completed concepts.

### `GET|POST /practice/<student_id>/<concept_id>`
Practice questions for a specific concept.

---

## 📊 Dashboard

### `GET /dashboard/<student_id>`
Student dashboard with charts, badges, and progress.

**Requirements:** Authenticated as `student_id`

### `GET /teacher-dashboard`
Teacher dashboard with class-level analytics and filters.

---

## 📚 Learning Content

### `GET /learning/<concept_id>`
Detailed learning content for a concept (6 sections).

### `GET|POST /feynman/<student_id>/<concept_id>`
Feynman technique board.

**GET:** Show the board with previous attempts.

**POST:** Submit explanation for AI evaluation.

**Form fields:** `explanation` (min 20 chars), `csrf_token`

---

## 🤖 AI & ML

### `GET /ml/metrics`
Public ML metrics dashboard (no auth required).

Shows: model performance, F1 scores, accuracy, cluster stats.

### `GET /ml/insights/<student_id>`
AI-driven insights page.

**Requirements:** Authenticated as `student_id`

Shows:
- Student cluster classification
- Risk prediction with SHAP explanations
- Recommended concepts
- RL-based learning suggestions

### `GET /chat`
AI chat assistant page.

**Requirements:** Authenticated

### `POST /chat/ask`
Send a message to the AI assistant.

**Content-Type:** `application/json`

**Body:**
```json
{"message": "Explain the difference between SQL and NoSQL"}
```

**Response:** `200` — JSON with AI answer

**Errors:**
- `400` — Missing or too-long message
- `503` — LLM not configured

---

## 📄 Reports

### `GET /report/<student_id>`
Generate and download PDF progress report.

**Requirements:** Authenticated as `student_id`

**Response:** PDF file (Content-Type: `application/pdf`)

---

## ⚙️ Utilities

### `GET /set-language/<lang>`
Switch UI language.

**Supported:** `en`, `ar`

**Response:** `302` redirect back

---

## 🔐 Authentication Model

The app uses **Flask session cookies**:

| Cookie | Flag | Purpose |
|--------|------|---------|
| `session` | `HttpOnly` | Cannot be accessed via JS |
| `session` | `Secure` | HTTPS only in production |
| `session` | `SameSite=Lax` | CSRF protection |

**Session lifetime:** 1 hour (configurable)

---

## 🚨 Error Responses

| Code | Meaning |
|------|---------|
| `200` | Success |
| `302` | Redirect (usually after POST) |
| `400` | Bad request (validation error) |
| `401` | Not authenticated |
| `403` | Unauthorized (wrong user) |
| `404` | Not found |
| `500` | Internal server error |
| `503` | Service unavailable (AI not configured) |

---

## 🛡️ CSRF Protection

All `POST` forms require a `csrf_token` field. Fetch it from any page's `
<input type="hidden" name="csrf_token">` field.

---

**Last updated:** 2026-09-20
