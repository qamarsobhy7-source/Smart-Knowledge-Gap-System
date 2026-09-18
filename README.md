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
[![Tests](https://img.shields.io/badge/Tests-9%2F9%20Passing-brightgreen)](#)

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
- [Testing](#-testing)
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
│   ├── init_database.py              # Automatic DB schema bootstrap
│   ├── database.py                   # SQLite operations
│   ├── backend_service.py            # Coordination layer
│   ├── diagnostic_engine.py          # Mastery & gap calculation
│   ├── priority_engine.py            # Priority ranking
│   ├── learning_path_engine.py       # Personalized path builder
│   ├── repository.py                 # CSV data loaders
│   ├── student_dashboard_service.py  # Student dashboard logic
│   └── teacher_dashboard_service.py  # Teacher dashboard logic
│
├── data/                             # Static datasets
│   ├── final_question_bank_270.csv   # 270 questions
│   ├── concepts_final.csv            # 45 concepts + prerequisites
│   ├── learning_content_FINAL.csv    # Learning material
│   └── practice_questions_FINAL.csv  # Practice questions
│
├── models/                           # ML support layer
│   └── ml_model_FINAL.joblib
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
├── .dockerignore
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile
├── LICENSE
├── README.md
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

## 🧪 Testing

The project includes a full end-to-end validation script that verifies:

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

**Current status:** ✅ **9 / 9 combinations passing** (3 subjects × 3 levels).

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
- [ ] Optional LLM-based explanation layer
- [ ] PDF export for results
- [ ] Multi-language support

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
