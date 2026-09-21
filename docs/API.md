# API Reference

Complete documentation of all HTTP endpoints in the **Smart Knowledge Gap System**.

**Base URL:** `https://smart-knowledge-gap-system-qqbms.faable.link`

---

## 📋 Table of Contents

- [Health & Monitoring](#-health--monitoring)
- [Authentication](#-authentication)
- [Assessment](#-assessment)
- [Dashboard](#-dashboard)
- [Learning Content](#-learning-content)
- [AI & ML](#-ai--ml)
- [Reports](#-reports)
- [SEO & Security Files](#-seo--security-files)
- [Utilities](#-utilities)
- [Rate Limiting](#-rate-limiting)

---

## 📌 Overview

**Base URL:** `https://smart-knowledge-gap-system-qqbms.faable.link`

**API Version:** `v1`

**Response Format:** All responses are `application/json` unless otherwise noted.

**Authentication:** Session-based for web pages, API key for `/chat/ask`.

**Error Handling:** See [Error Responses](#-error-responses) below.

---

## 🩺 Health & Monitoring

### `GET /health`
Enhanced health check endpoint for monitoring and load balancers.

**Response:** `200 OK` — JSON

```json
{
  "status": "healthy",
  "service": "smart-knowledge-gap-system",
  "version": "1.0.8",
  "timestamp": 1789948244,
  "datetime": "2026-09-21T12:30:44.123Z",
  "services": {
    "database": {"status": "connected", "type": "postgresql"},
    "qdrant": {"status": "configured"},
    "groq": {"status": "configured"},
    "ml_models": {"status": "loaded", "count": 9}
  }
}
```

**Status values:**
- `healthy` — All critical services running
- `degraded` — Some services unavailable

### `GET /api/version`
Returns API version and build information.

**Response:** `200 OK` — JSON

```json
{
  "name": "Smart Knowledge Gap System",
  "version": "1.0.8",
  "api_version": "v1",
  "build_date": "2026-09-21",
  "environment": "production",
  "python_version": "3.11.3",
  "framework": "Flask 3.1",
  "links": {
    "github": "https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System",
    "demo": "https://smart-knowledge-gap-system-qqbms.faable.link",
    "video": "https://qamarsobhy7-source.github.io/Smart-Knowledge-Gap-System/"
  }
}
```

**Note:** All responses include `X-Response-Time` header (e.g., `0.6ms`).

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

## 🔍 SEO & Security Files

### `GET /robots.txt`
Crawl rules for search engines.

**Response:** `200 OK` — `text/plain`

### `GET /sitemap.xml`
Sitemap for search engine indexing (5 URLs).

**Response:** `200 OK` — `application/xml`

### `GET /security.txt`
Security contact information (RFC 9116 compliant).

**Response:** `200 OK` — `text/plain`

### `GET /.well-known/security.txt`
Alternative location for security.txt (RFC 9116 standard).

**Response:** `200 OK` — `text/plain`

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

---

## ⏱️ Rate Limiting

Flask-Limiter protects endpoints from abuse.

### Limits

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `POST /login` | 30/min | Brute-force protection |
| `POST /register` | 10/min | Spam protection |
| `GET/POST /forgot-password` | 10/min | Email abuse protection |
| `POST /reset-password/<token>` | 5/min | Token abuse protection |
| `POST /chat/ask` | 15/min | AI abuse protection |
| **Global default** | 200/day, 60/hour | Overall protection |

### Response on Limit

**Status:** `429 Too Many Requests`

```json
{
  "error": "Rate limit exceeded. Please try again later."
}
```

### Notes
- Rate limiter is **disabled** in `TESTING` mode
- Uses **in-memory** storage (per-instance)
- Identification via **remote IP address**

---

**Last updated:** 2026-09-21
