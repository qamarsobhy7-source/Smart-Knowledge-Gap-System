# 🎓 Smart Knowledge Gap & Personalized Learning System

<div align="center">

**A concept-level diagnostic and personalized learning platform
that identifies knowledge gaps, prioritizes learning needs,
and generates prerequisite-aware learning paths.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.2-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](#)
[![Tests](https://img.shields.io/badge/Tests-22%2F22%20Passing-brightgreen)](#)
[![CI](https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System/actions/workflows/ci.yml/badge.svg)](https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](#)
[![i18n](https://img.shields.io/badge/i18n-EN%20%7C%20AR-blue)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supported-336791?logo=postgresql&logoColor=white)](#)
[![ML](https://img.shields.io/badge/Machine%20Learning-RandomForest%20%7C%20GradientBoosting-orange)](#)

</div>

---

## 🚀 Live Demo

**[🔗 Try the app live →](https://smart-knowledge-gap-system-qqbms.faable.link/)**

https://smart-knowledge-gap-system-qqbms.faable.link/

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [Question Bank](#-question-bank)
- [Diagnostic Engine](#-diagnostic-engine)
- [Knowledge Graph & Priorities](#-knowledge-graph--priorities)
- [Learning Path](#-learning-path)
- [Screenshots](#-screenshots)
- [Machine Learning Layer](#-machine-learning-layer)
- [Testing](#-testing)
- [Docker](#-docker)
- [Data Persistence](#-data-persistence)
- [Deployment](#-deployment)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---
## 🌟 Overview

Traditional assessment systems often rely on a single total score.
This project goes far beyond that.

The **Smart Knowledge Gap & Personalized Learning System** is a Flask-based web application that:

1. Diagnoses a student's performance **concept by concept** — not just overall.
2. Detects **knowledge gaps** in specific concepts.
3. Classifies each concept into mastery levels (`Strong`, `Adequate`, `Weak`, `Critical`).
4. Uses a **knowledge graph with prerequisites** to determine which concepts should be learned first.
5. Generates a **personalized learning path** tailored to the student's current mastery.
6. Provides **learning content and practice questions** for each weak concept.
7. Performs a **re-assessment** and computes the **before vs after improvement** to prove that learning actually happened.

The system currently covers three academic subjects:

| Subject | Concepts | Questions |
|---|---|---|
| **Mathematics** | 15 | 90 |
| **Physics** | 15 | 90 |
| **Computer Science** | 15 | 90 |
| **Total** | **45** | **270** |

---

## ✨ Key Features

### 🎯 Concept-Level Diagnosis

Instead of one overall score, the system produces a mastery percentage for **every concept** the student was assessed on.

### 🧠 Six Question Types per Concept

Every concept is evaluated through 6 complementary question types:

| Type | Purpose |
|---|---|
| **Understanding** | Tests conceptual comprehension |
| **Application** | Tests ability to apply the concept |
| **Reasoning** | Tests logical reasoning |
| **Problem Solving** | Tests multi-step problem solving |
| **Misconception Detection** | Tests ability to identify wrong reasoning |
| **Transfer** | Tests ability to apply the concept in a new context |

### 🔗 Prerequisite-Aware Knowledge Graph

The system knows that, for example, *Data Structures* comes before *Algorithm Analysis*. When a student struggles with an advanced concept, the engine checks whether a **prerequisite concept** is also weak and prioritizes the prerequisite first.

### 📊 Mastery Classification

Each concept is classified into one of four levels:

| Level | Mastery Range | Meaning |
|---|---|---|
| **Strong** | 80% – 100% | Concept is well mastered |
| **Adequate** | 60% – 79% | Concept is acceptable |
| **Weak** | 40% – 59% | Concept needs improvement |
| **Critical** | 0% – 39% | Concept is a critical gap |

### 🎯 Priority Engine

Not all gaps are equal. The priority engine ranks concepts using a combination of mastery, gap score, and prerequisite depth.

### 🛤️ Personalized Learning Path

Each student receives a **unique learning path** ordered by priority and prerequisite dependencies — no two students see the same path.

### 📚 Learning Content & Practice

For every weak concept the student receives:

- A structured explanation
- Key points to remember
- Practice questions for reinforcement

### 👩‍🏫 Teacher Dashboard

Teachers get class-level analytics:

- Number of students
- Average mastery per subject
- At-risk students
- Hardest concepts
- Average improvement across the class

### 📈 Before vs After Improvement

After completing the learning path, the student takes a **re-assessment**. The system then computes:

```
Improvement = After Mastery - Before Mastery
```

and displays the delta per concept.

### 🔐 Authentication & Password Reset

- Email + password registration with hashed passwords (Werkzeug)
- Session-based login and logout
- Password reset flow with time-limited tokens (1h TTL)
- Duplicate-email and weak-password validation

### 📊 Interactive Dashboard Charts

- **Doughnut chart** — mastery distribution
- **Bar chart** — per-concept mastery comparison
- Powered by **Chart.js**

### 🏆 Achievements & Badges

Eight unlockable achievements: First Steps, Perfect Score, Strong Mind, Bookworm, Sharp Shooter, On the Rise, Master, Expert.

### 📄 PDF Report Export

Complete per-student report generated with **ReportLab**.

### 🔍 Teacher Dashboard Filters

Filter by **Subject**, **Level**, or **Status**.

### 🌍 Multi-language (English + Arabic)

- Full UI translation in **English** and **Arabic**
- Automatic **RTL** layout for Arabic
- Language switcher in the navbar

### 🐘 PostgreSQL + SQLite Support

- Runs on **SQLite** by default
- Switch to **PostgreSQL** by setting `DATABASE_URL`
- Same public API, no code changes

### ⚙️ Error Handling & Logging

- Custom **404** and **500** pages
- Structured logging to console and rotating file

### 🛡️ Security

- **CSRF protection** on all forms
- Hashed passwords
- Session cleanup
- Generic reset error messages

---
## 🔄 How It Works

```
Student Registration (Name + Age + Subject + Level)
        ↓
Diagnostic Assessment (30 questions for chosen subject + level)
        ↓
Concept-Level Scoring (Mastery · Gap Level · Gap Score)
        ↓
Knowledge Graph Analysis (Prerequisites · Priorities)
        ↓
Personalized Learning Path (Ordered by priority)
        ↓
Learning Content & Practice (Per weak concept)
        ↓
Re-assessment (Same 30 questions)
        ↓
Before vs After (Improvement Analysis)
```

---

## 🏗️ Architecture

The system follows a clean **layered architecture**:

```
┌──────────────────────────────────────────────┐
│              Presentation Layer              │
│   Flask Routes  +  Jinja2 Templates          │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│              Service Layer                   │
│   BackendService                             │
│   StudentDashboardService                    │
│   TeacherDashboardService                    │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│              Engine Layer                    │
│   DiagnosticEngine  (mastery & gaps)         │
│   PriorityEngine    (ranking)                │
│   LearningPathEngine (personalization)       │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│              Data Access Layer               │
│   Repository  (CSV loaders)                  │
│   Database    (SQLite — 7 tables)            │
│   init_database (schema bootstrap)           │
└─────────────────────┬────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│              Data Layer                      │
│   270 questions · 45 concepts                │
│   Learning content · Practice questions      │
└──────────────────────────────────────────────┘
```

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11+ |
| **Web Framework** | Flask 3.1 |
| **Templating** | Jinja2 |
| **Data** | pandas 2.2, NumPy |
| **ML Support** | scikit-learn, joblib |
| **Database** | SQLite 3 |
| **Frontend** | HTML5, CSS3, vanilla JavaScript |
| **Testing** | Flask test client, pytest |
| **Deployment** | Docker, Gunicorn |
| **Hosting** | Faable |

---

## 📁 Project Structure

```
smart-knowledge-gap/
│
├── app/                              # Backend application
│   ├── app.py                        # Flask routes (entry point)
│   ├── init_database.py              # DB schema bootstrap
│   ├── database.py                   # SQLite/PostgreSQL ops
│   ├── backend_service.py            # Coordination layer
│   ├── diagnostic_engine.py          # Mastery & gap calculation
│   ├── priority_engine.py            # Priority ranking
│   ├── learning_path_engine.py       # Personalized path builder
│   ├── repository.py                 # CSV data loaders
│   ├── pdf_report.py                 # PDF report generation
│   ├── translations.py               # i18n (EN + AR)
│   ├── student_dashboard_service.py  # Student dashboard
│   ├── teacher_dashboard_service.py  # Teacher dashboard
│   │
│   └── ml/                           # AI/ML layer (8 models)
│       ├── train_all.py              # One-command training
│       ├── ml_service.py             # Unified interface
│       ├── risk_predictor.py         # Gradient Boosting
│       ├── performance_predictor.py  # Random Forest
│       ├── concept_recommender.py    # Hybrid recommender
│       ├── student_clusterer.py      # K-Means + PCA
│       ├── knowledge_tracing.py      # LSTM
│       ├── rl_environment.py         # RL environment
│       ├── rl_dqn_agent.py           # DQN agent
│       ├── explainability.py         # SHAP
│       ├── rag_engine.py             # Vector store
│       ├── llm_service.py            # Groq + RAG
│       ├── data_generator.py         # Synthetic data
│       └── sequence_data_generator.py
│
├── data/                             # Static datasets
│   ├── final_question_bank_270.csv   # 270 questions
│   ├── concepts_final.csv            # 45 concepts + prerequisites
│   ├── learning_content_FINAL.csv    # Learning material
│   └── practice_questions_FINAL.csv  # Practice questions
│
├── app/ml/                           # Machine Learning layer
│   ├── data_generator.py
│   ├── risk_predictor.py
│   ├── performance_predictor.py
│   ├── concept_recommender.py
│   ├── student_clusterer.py
│   └── ml_service.py
│
├── models/                           # Trained ML models (regenerable)
│   ├── student_risk_model.joblib     # Generated by train_all.py
│   ├── student_performance_model.joblib
│   ├── concept_recommender.joblib
│   ├── student_clusterer.joblib
│   ├── knowledge_tracing_model.pt
│   ├── rl_dqn_agent.pt
│   ├── vector_db/                    # RAG Qdrant Cloud store
│   └── metrics/                      # Model metrics
│
├── templates/                        # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── assessment.html
│   ├── results.html
│   ├── student_dashboard.html
│   ├── teacher_dashboard.html
│   ├── learning_content.html
│   ├── practice.html
│   ├── 404.html
│   └── 500.html
│
├── static/                           # Frontend assets
│   └── style.css
│
├── screenshots/                      # README screenshots
│
├── tests/                            # End-to-end validation
│   └── test_full_flow.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .dockerignore
├── .env.docker
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile
├── LICENSE
├── Makefile
├── README.md
├── docker-compose.yml
└── requirements.txt
```

---
## 🚀 Getting Started

### Prerequisites

- **Python** 3.11 or higher
- **pip** (bundled with Python)
- **Git**
- Optional: **Docker**

### 1. Clone the Repository

```bash
git clone https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System.git
cd Smart-Knowledge-Gap-System
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
.venv\Scripts\activate          # Windows
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Generate a strong secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output into `SECRET_KEY=` in `.env`.

### 5. Initialize the Database

The schema is created automatically on first run, but you can also initialize it manually:

```bash
python -m app.init_database
```

This creates `data/smart_knowledge_gap.db` with all 7 required tables.

### 6. Run the Application

```bash
python app/app.py
```

Then open your browser at `http://localhost:5000`.

---

## 🎮 Usage

### Student Flow

1. **Register** — Enter name, age, subject, level.
2. **Take the Diagnostic Assessment** — Answer 30 questions.
3. **View Results** — See mastery per concept, strengths, gaps.
4. **Follow the Learning Path** — Open each recommended concept.
5. **Read Learning Content** — Study the concept.
6. **Practice** — Answer 6 practice questions.
7. **Re-assessment** — Retake the diagnostic.
8. **Compare Before vs After** — See improvement per concept.

### Teacher Flow

1. Open `/teacher-dashboard`.
2. View: number of students, average mastery, at-risk students, hardest concepts, average improvement.

---

## 📚 Question Bank

| Metric | Value |
|---|---|
| Subjects | 3 |
| Levels per subject | 3 |
| Concepts per level | 5 |
| Concepts per subject | 15 |
| Questions per concept | 6 |
| Total concepts | **45** |
| Total questions | **270** |

### Distribution per Subject

| Level | Concepts | Questions |
|---|---|---|
| Beginner | 5 | 30 |
| Intermediate | 5 | 30 |
| Advanced | 5 | 30 |
| **Total** | **15** | **90** |

### Question Types per Concept

Every concept has exactly 6 questions, one of each type:

1. Understanding
2. Application
3. Reasoning
4. Problem Solving
5. Misconception Detection
6. Transfer

### Schema

| Column | Description |
|---|---|
| `subject_id` | 1 = Mathematics, 2 = Physics, 3 = Computer Science |
| `concept_id` | Unique concept identifier (1–45) |
| `concept_name` | Human-readable concept name |
| `difficulty` | Beginner / Intermediate / Advanced |
| `question_type` | One of the six question types |
| `question_id` | Unique question identifier |
| `question_text` | The question itself |
| `option_a` – `option_d` | The four answer options |
| `correct_answer` | One of A / B / C / D |

---

## 🧠 Diagnostic Engine

For every concept, the engine computes:

```
Mastery   = Weighted average of question-type scores × 100
Gap Score = 100 − Mastery
Gap Level = Strong | Adequate | Weak | Critical
```

Weights are equally distributed across the six question types, so a student who understands a concept but cannot apply it receives a **partial** mastery score — which is more accurate than a single correct/total ratio.

---

## 🔗 Knowledge Graph & Priorities

The file `data/concepts_final.csv` stores, for every concept:

- Subject
- Concept name
- Difficulty
- **Prerequisite concept IDs**

The **Priority Engine** combines:

1. Gap score (higher gap = higher priority)
2. Prerequisite depth (foundational concepts first)
3. Mastery level (Critical before Weak)

to produce a **ranked list of concepts to study first**.

---

## 🛤️ Learning Path

The learning path is generated from:

- The ranked priority list
- The student's current mastery per concept
- The prerequisite graph

Concepts already mastered are skipped. Prerequisite concepts that are weak are inserted **before** their dependents.

The result is a **personalized, ordered list of concepts** that the student should follow.

---
## 🤖 Machine Learning Layer

The system includes a dedicated AI/ML layer that provides **predictive analytics** on top of the rule-based diagnostic engine.

> **Important:** All models are trained on **synthetic development data** generated from the real question bank. Metrics are reported as **Development Evaluation** — not as claims of real-world performance.

### 🎯 Models

| Model | Type | Purpose |
|---|---|---|
| **Risk Predictor** | Gradient Boosting (binary) | Predicts whether a student is **At Risk** (mastery < 60%) on a concept |
| **Performance Predictor** | Random Forest (multi-class) | Predicts target status: Critical / Weak / Adequate / Strong |
| **Concept Recommender** | Hybrid (content + collaborative + prerequisite-aware) | Recommends next concepts to study |
| **Student Clusterer** | K-Means + PCA | Groups students into interpretable clusters |

### 📊 Model Performance

**Risk Predictor (binary classification):**

| Metric | Value |
|---|---|
| Accuracy | **83.87%** |
| Precision | **86.76%** |
| Recall | **92.71%** |
| F1 Score | **89.63%** |
| ROC-AUC | **87.95%** |

**Student Clusterer:**

- **2,000 students** → **4 clusters**
- Silhouette score: **0.17**
- PCA variance explained: **53.6%** (2 components)

**Clusters identified:**

| Cluster | Size | Avg Mastery |
|---|---|---|
| High Performers | 549 | 64.0% |
| Steady Learners | 324 | 45.1% |
| Struggling Students | 529 | 36.2% |
| Improving Students | 598 | 35.2% |

### 🧠 Feature Engineering

The models are trained on the following features (per student, per concept):

- Subject ID
- Concept difficulty (encoded: Beginner / Intermediate / Advanced)
- Number of practice sessions
- Average response time
- Reassessment participation
- Improvement between assessments
- Question accuracy

### 🔧 Training Pipeline

```bash
# 1. Generate synthetic training data
python -c "from ml.data_generator import save_synthetic_dataset; save_synthetic_dataset()"

# 2. Train all models
python -c "
import pandas as pd
from ml.risk_predictor import train_risk_predictor, save_risk_predictor
from ml.performance_predictor import train_performance_predictor, save_performance_predictor
from ml.concept_recommender import train_recommender, save_recommender
from ml.student_clusterer import train_clusterer, save_clusterer

df = pd.read_csv('data/synthetic_ml_training_data.csv')
concepts = pd.read_csv('data/concepts_final.csv')
qb = pd.read_csv('data/final_question_bank_270.csv')

save_risk_predictor(train_risk_predictor(df))
save_performance_predictor(train_performance_predictor(df))
save_recommender(train_recommender(df, concepts, qb))
save_clusterer(train_clusterer(df))
"
```

### 📈 ML Insights Dashboard

Every student has access to a personal **AI Insights** page (`/ml/insights/<student_id>`) that shows:

- Their **learning cluster** (High Performers / Steady Learners / ...)
- **Per-concept risk predictions** (At Risk / On Track)
- **AI-recommended next concepts** to study

Public model metrics are visible at `/ml/metrics`.

### 🏗️ ML Architecture

```
app/ml/
├── __init__.py
├── config.py                    # Centralized configuration
├── data_generator.py            # Synthetic data generation
├── risk_predictor.py            # Binary classification
├── performance_predictor.py     # Multi-class classification
├── concept_recommender.py       # Hybrid recommender
├── student_clusterer.py         # K-Means + PCA
└── ml_service.py                # Unified interface for Flask
```

---

## 📸 Screenshots

A quick visual tour of the platform.

### 🏠 Home Page

![Home Page](screenshots/01-home.png)

*Clean, modern landing page with subject & level selection.*

### 📝 Diagnostic Assessment

![Assessment](screenshots/02-assessment.png)

*Concept-by-concept assessment with shuffled questions.*

### 📊 Results — Knowledge Profile

![Results](screenshots/03-results.png)

*Per-concept mastery with Strong / Adequate / Weak / Critical levels.*

### 🎯 Learning Priorities

![Learning Priorities](screenshots/04-learning-priorities.png)

*Ranked concepts to focus on first, based on gap and prerequisites.*

### 🛤️ Personalized Learning Path

![Learning Path](screenshots/05-learning-path.png)

*Ordered list of concepts the student should study next.*

### 👤 Student Dashboard

![Student Dashboard](screenshots/06-student-dashboard.png)

*Overall mastery, strengths, gaps, practice activity, and progress.*

### 📚 Learning Content

![Learning Content](screenshots/07-learning-content.png)

*Structured explanation, key points, and examples per concept.*

### 🎯 Practice Mode

![Practice](screenshots/08-practice.png)

*Targeted practice with instant scoring and feedback.*

### 👩‍🏫 Teacher Dashboard

![Teacher Dashboard](screenshots/09-teacher-dashboard.png)

*Class-level analytics: student performance, concepts, and priorities.*

### 🌙 Dark Mode

![Dark Mode](screenshots/10-dark-mode.png)

*Full dark mode support with seamless theme switching.*

---

## 🔧 Reproducing the AI/ML Layer

The trained ML models and synthetic datasets are **not committed** to this
repository (they total ~75 MB and are fully regenerable). To rebuild them:

```bash
# One command to train all 8 models from scratch
python -m app.ml.train_all
```

This will:

1. Generate synthetic training data
2. Train the **Risk Predictor** (Gradient Boosting)
3. Train the **Performance Predictor** (Random Forest)
4. Build the **Concept Recommender** (Hybrid)
5. Train the **Student Clusterer** (K-Means + PCA)
6. Train the **Knowledge Tracing** model (LSTM)
7. Train the **RL Agent** (DQN)
8. Build the **RAG vector store** (Qdrant Cloud)

**Total time:** ~5-8 minutes on CPU.

Once complete, all model artifacts will be available in `models/` and the
live app will automatically detect and use them.

> **Why not committed?**
> Keeping large binaries out of Git keeps the repository lightweight
> (~5 MB clone) and ensures the pipeline is fully reproducible from code.

---

## 🧪 Testing

### 1. End-to-end validation script

This script verifies:

- Student registration
- Subject and level filtering
- Display of the correct 30 questions
- Answer submission
- Answer scoring (30/30 when all answers are correct)
- Concept-level diagnosis
- Priority calculation
- Learning path generation
- Re-assessment and improvement calculation

Run it with:

```bash
python tests/test_full_flow.py
```

**Status:** ✅ **9 / 9 combinations passing** (3 subjects × 3 levels).

### 2. Continuous Integration (GitHub Actions)

Every push runs `.github/workflows/ci.yml`:

- Multi-version Python matrix (**3.11** and **3.12**)
- Question bank integrity checks (270 questions, 45 concepts)
- Learning content integrity checks
- Database initialization
- Flask smoke tests (home, login, teacher dashboard, 404)

**Status:** ✅ Passing on both Python versions.

---

## 🐳 Docker

### Quick Start

```bash
cp .env.docker .env
docker compose up -d
```

### Make targets

```bash
make help          # Show all commands
make install       # Install dependencies
make run           # Run Flask dev server
make test          # Run tests
make docker-build  # Build Docker image
make docker-up     # Start compose
make docker-down   # Stop compose
```

### PostgreSQL via Docker

Uncomment the `db` service in `docker-compose.yml`, then add `DATABASE_URL` to `.env`.

---

## 💾 Data Persistence

| Backend | When to use | Persistence |
|---|---|---|
| **SQLite** (default) | Local dev, demos | Lost on restart |
| **PostgreSQL** | Production | Persists forever |

Switch to PostgreSQL:

```bash
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
```

The app detects `DATABASE_URL` at startup and uses the correct backend automatically.

---

## 🐳 Deployment

### Option 1 — Docker

```bash
docker build -t smart-knowledge-gap .
docker run -p 5000:5000 --env-file .env smart-knowledge-gap
```

### Option 2 — Gunicorn (Production)

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app.app:app
```

### Option 3 — Faable (Live)

The application is currently deployed on Faable:

🔗 **Live Demo:** [https://smart-knowledge-gap-system-qqbms.faable.link/](https://smart-knowledge-gap-system-qqbms.faable.link/)

---

## 🗺️ Roadmap

- [x] Concept-level diagnostic engine
- [x] Knowledge graph with prerequisites
- [x] Priority engine
- [x] Personalized learning path
- [x] Re-assessment & improvement analysis
- [x] Student & teacher dashboards
- [x] Automatic database initialization
- [x] Full end-to-end testing
- [x] Modern UI with dark mode
- [x] Error pages (404, 500)
- [x] Logging system
- [x] CSRF protection
- [x] Question shuffling per assessment
- [x] Email + password authentication
- [x] Password reset flow
- [x] Enriched learning content (6 sections per concept)
- [x] PDF report export
- [x] Interactive dashboard charts
- [x] Teacher dashboard filters
- [x] Achievements & badges
- [x] Multi-language (English + Arabic with RTL)
- [x] PostgreSQL support (with SQLite fallback)
- [x] GitHub Actions CI
- [x] Docker Compose
- [x] **Machine Learning layer** (Risk Predictor + Performance Predictor + Recommender + Clusterer)
- [x] **AI Insights Dashboard** (per-student ML predictions)
- [ ] Optional LLM-based explanation layer
- [ ] Email notifications

---

## 🤝 Contributing

Contributions are welcome!
Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👩‍💻 Author

**Qamar Sobhy**

GitHub: [@qamarsobhy7-source](https://github.com/qamarsobhy7-source)

Built as a complete demonstration of concept-level diagnostic and personalized learning design.

---

<div align="center">

**⭐ If you find this project useful, please give it a star! ⭐**

Made with ❤️ using Flask, pandas, and scikit-learn.

</div>
