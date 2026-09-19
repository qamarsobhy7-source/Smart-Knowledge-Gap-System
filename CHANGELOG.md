# Changelog

All notable changes to **Smart Knowledge Gap System** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-09-20

### 🎉 First Stable Production Release

The complete, production-ready release of the Smart Knowledge Gap System.

#### ✨ Added

**Core Learning Engine**
- Adaptive assessment system with 270-question bank
- Concept-level knowledge gap detection
- Prerequisite-aware personalized learning paths
- Feynman technique board with AI evaluation
- Reassessment loop tracking student growth

**Machine Learning (8 Models)**
- Risk Predictor (Gradient Boosting) — F1 = 89.63%
- Performance Predictor (Random Forest, 4-class)
- Concept Recommender (Hybrid filtering)
- Student Clusterer (K-Means + PCA, 4 clusters)
- Knowledge Tracing (LSTM) — Acc = 70.83%
- SHAP Explainer for per-prediction transparency
- LLM + RAG Assistant (Groq + Qdrant, 675 documents)
- RL Agent (DQN) for adaptive question selection

**Authentication & Security**
- User registration, login, logout
- Password reset via email
- CSRF protection on all forms
- Session hardening (HttpOnly, Secure, SameSite=Lax)
- Werkzeug PBKDF2 password hashing

**User Interface**
- Student dashboard with charts (Chart.js)
- Teacher dashboard with filters
- AI Insights page (clusters, SHAP, recommendations)
- ML Metrics public page
- Multi-language support (English + Arabic RTL)
- Dark mode toggle across all pages
- Achievements & badges system (8 badges)
- Custom 404 & 500 error pages
- PDF progress reports (ReportLab)

**Infrastructure**
- PostgreSQL (Supabase Cloud) with SQLite fallback
- Qdrant Cloud vector database
- FastEmbed lightweight ONNX embeddings
- Docker + docker-compose + Makefile
- GitHub Actions CI pipeline
- Structured logging with rotating file handler
- Test suite (57 tests, 100% passing)

**Documentation**
- Comprehensive README with badges
- 13 application screenshots
- Demo video (GitHub Pages playable)
- Research paper (8 sections, 20 references)
- CONTRIBUTING.md guide
- SECURITY.md policy
- MIT License

**Deployment**
- Faable Cloud hosting (Python 3.11)
- Gunicorn WSGI server
- GitHub Pages video player
- Auto-deploy on push to master

---

## [0.9.0] — 2026-09-19

### 🚀 Pre-release Polish

#### Added
- Live deployment on Faable Cloud
- Qdrant Cloud migration (from ChromaDB, 675 docs)
- FastEmbed migration (from sentence-transformers)
- Full screenshot set (13 images)
- Demo video recording & hosting

#### Fixed
- `/register` GET route (405 → 200 redirect)
- Session persistence on HTTPS (Secure cookies)
- Shuffle state reset on new assessment

#### Changed
- Chat header: Gemini → Groq branding
- Screenshot compression (65% size reduction)
- Torch-safe imports for production

---

## [0.8.0] — 2026-09-17

### 🧪 Test Suite & Repo Cleanup

#### Added
- Comprehensive test suite (57 tests, 100% passing)
- `train_all.py` script for rebuilding ML models
- GitHub Actions CI workflow

#### Changed
- Repository cleanup: removed 73 backup files
- Repo size reduced: 75 MB → 5 MB

---

## [0.7.0] — 2026-09-14

### 📄 Research Paper

#### Added
- Research paper draft (`docs/research_paper.md`, 31 KB)
- 8 sections covering motivation → evaluation → future work
- 20 academic references
- Demo video script (`docs/demo_video_script.md`)

---

## [0.6.0] — 2026-09-10

### 🤖 AI Integrations

#### Added
- Feynman Board with AI explanation evaluation
- AI Chat assistant (Groq LLM + RAG)
- AI Insights page (clustering, SHAP, RL recommendations)
- ML Metrics public page

---

## [0.5.0] — 2026-09-05

### 🧠 Machine Learning Layer

#### Added
- 8 ML models trained & integrated
- Risk Predictor (F1 = 89.63%)
- Performance Predictor (Random Forest)
- Concept Recommender (Hybrid)
- Student Clusterer (K-Means + PCA)
- Knowledge Tracing (LSTM)
- SHAP explainer for transparency
- RL Agent (DQN)

---

## [0.4.0] — 2026-08-28

### 🏗️ Software Engineering

#### Added
- PDF report generation (ReportLab)
- PostgreSQL + SQLite dual support
- GitHub Actions CI pipeline
- Docker + docker-compose + Makefile
- Structured logging system
- CSRF protection on all forms
- Automatic session cleanup

---

## [0.3.0] — 2026-08-20

### 🎨 UI/UX Enhancements

#### Added
- Dashboard charts (Doughnut + Bar)
- 8 unlockable achievements & badges
- Teacher dashboard with filters
- Multi-language: English + Arabic (full RTL)
- Custom 404 & 500 error pages
- Dark mode toggle

---

## [0.2.0] — 2026-08-15

### 📚 Learning Content Enrichment

#### Added
- 45 concepts × 6 learning sections each:
  - Why It Matters
  - Step-by-Step Explanation
  - Worked Examples
  - Common Mistakes
  - Study Tips
  - What's Next

---

## [0.1.0] — 2026-08-10

### 🔐 Authentication & Foundation

#### Added
- User registration, login, logout
- Password reset via email
- Email validation + password hashing

---

## [0.0.1] — 2026-08-01

### 🎯 Initial Commit

#### Added
- Project scaffolding
- Basic Flask app structure
- Question bank CSV (270 questions)
- Core database schema

#### Fixed
- Scoring bug (7/30 → 30/30 correct)
- Physics questions translated to English
- Answer distribution balanced (68/68/67/67)

---

## Links

- **Repository:** https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System
- **Live Demo:** https://smart-knowledge-gap-system-qqbms.faable.link
- **Video:** https://qamarsobhy7-source.github.io/Smart-Knowledge-Gap-System/
- **Releases:** https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System/releases

---

**Legend:** 🎉 Release · 🚀 Feature · 🐛 Fix · 📚 Docs · 🤖 ML · 🎨 UI · 🔐 Security
