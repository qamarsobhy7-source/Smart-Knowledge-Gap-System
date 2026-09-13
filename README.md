# Smart Knowledge Gap & Personalized Learning System

A web-based personalized learning system that analyzes student performance at the concept level, identifies knowledge gaps, prioritizes learning needs, and generates prerequisite-aware personalized learning paths.

The system is designed for three academic subjects:

- Mathematics
- Physics
- Computer Science

## Overview

Traditional assessment systems often rely mainly on overall scores. This project focuses on concept-level diagnosis.

The system evaluates student performance across individual concepts and determines:

- Which concepts are strong
- Which concepts require improvement
- Which concepts represent critical knowledge gaps
- Which concepts should be prioritized first
- Which prerequisite concepts should be addressed before dependent concepts
- How mastery changes after learning and reassessment

The core workflow is:

**Student → Registration → Subject & Level Selection → 30-Question Diagnostic → Concept-Level Diagnosis → Mastery & Knowledge Gaps → Knowledge Graph → Priority Calculation → Personalized Learning Path → Learning Content & Practice → Reassessment → Improvement Analysis**

## System Scope

The current system contains:

- 3 subjects
- 3 educational levels per subject
- 45 concepts
- 270 diagnostic questions
- 270 practice questions
- 6 question types per concept
- 6 questions per concept in the diagnostic question bank

Each subject contains:

- 5 Beginner concepts
- 5 Intermediate concepts
- 5 Advanced concepts

### Diagnostic Assessment Design

A diagnostic assessment uses **one selected subject and one selected educational level**.

Each assessment contains exactly:

**5 concepts × 6 question types = 30 questions**

The six question types are:

1. Understanding
2. Application
3. Reasoning
4. Problem Solving
5. Misconception Detection
6. Transfer

Subject and educational level are never mixed within the same diagnostic assessment.

The 270-question dataset represents the complete diagnostic question bank across all subjects and educational levels. It is not the number of questions submitted by a student in one assessment.


## Core Components

### 1. Diagnostic Assessment

The diagnostic engine processes student answers and calculates concept-level mastery rather than relying only on a total score.

Each concept is evaluated independently, allowing a student to demonstrate strong performance in some concepts while having gaps in others.

### 2. Knowledge Gap Detection

The system classifies concept mastery and identifies learning gaps.

Mastery states are diagnosed from assessment performance rather than selected manually by the student.

Knowledge gaps are represented at the concept level and are considered when determining learning priorities.

### 3. Knowledge Graph

The system contains prerequisite relationships between concepts.

The knowledge graph helps determine the appropriate learning order and prevents dependent concepts from being prioritized before required prerequisite concepts.

### 4. Priority Engine

Learning priorities are calculated from diagnosed concept mastery and prerequisite relationships.

This allows the system to identify which concepts should receive attention first and which prerequisite gaps may be blocking progress.

### 5. Personalized Learning Path

The learning path is generated from the student's diagnosed learning needs.

The path is prerequisite-aware and produces an ordered sequence of learning targets for the selected subject.

### 6. Learning Content and Practice

Each concept is connected to structured learning content and practice questions.

The practice question bank contains 270 questions covering the same six question types used to support concept-level practice.

### 7. Reassessment and Improvement

After learning and practice, students can be reassessed.

The system compares before and after mastery values to measure learning improvement at the concept level.

### 8. Student Dashboard

The student dashboard provides information about:

- Diagnostic performance
- Concept mastery
- Knowledge gaps
- Learning priorities
- Personalized learning path
- Practice activity
- Reassessment results
- Learning improvement

### 9. Teacher Dashboard

The teacher dashboard provides an overview of student performance, including:

- Student performance
- Assessment history
- Concept-level performance
- Knowledge gaps
- Learning priorities
- Learning progress
- Practice activity
- Reassessment results
- Before/after improvement


## Architecture

The system follows a modular architecture that separates the web layer, educational logic, persistence, dashboards, and supporting machine learning.

The main learning pipeline is:

Student
   |
   v
Registration
   |
   v
Subject + Educational Level
   |
   v
30-Question Diagnostic Assessment
   |
   v
Concept-Level Mastery Diagnosis
   |
   v
Knowledge Gap Detection
   |
   v
Knowledge Graph + Priority Engine
   |
   v
Personalized Learning Path
   |
   +----------------------+
   |                      |
   v                      v
Learning Content       Practice
   |                      |
   +----------+-----------+
              |
              v
        Reassessment
              |
              v
   Before/After Improvement

The Flask application provides the web layer, while dedicated backend services and engines handle assessment processing, diagnosis, prioritization, learning paths, persistence, and dashboard data.

## Supporting Machine Learning Layer

The project includes a machine learning prediction layer as a supporting component.

ML is not the sole authority for educational diagnosis. The core diagnostic workflow is concept-based and deterministic.

The application runtime does not depend on the stored ML model for its core assessment and diagnosis flow.

The stored ML artifacts include:

- ML configuration
- Trained model
- Evaluation metrics
- Development prediction artifacts

The current ML evaluation is classified as **Development Evaluation**.

The development dataset is synthetic and is intended for system development and evaluation. Reported metrics must not be interpreted as evidence of real-world educational performance.


## Data Layer

The project includes:

- 270-question diagnostic question bank
- 45 concepts
- Learning content for 45 concepts
- 270 practice questions
- Personalized learning path data
- Priority profiles
- Before/after improvement data
- Progress summary
- SQLite application database

The production SQLite database is maintained as a prebuilt empty database containing the validated application schema.

## Technology Stack

### Backend

- Python
- Flask
- SQLite

### Data Processing

- pandas

### Frontend

- HTML
- CSS
- Jinja templates

### Machine Learning

- Offline supporting ML artifacts
- scikit-learn-compatible serialized model

The ML artifacts are not required by the core application runtime.

## Project Structure

app/
├── __init__.py
├── app.py
├── backend_contract_FINAL.json
├── backend_service.py
├── database.py
├── diagnostic_engine.py
├── learning_path_engine.py
├── priority_engine.py
├── repository.py
├── student_dashboard_contract_FINAL.json
├── student_dashboard_service.py
├── teacher_dashboard_contract_FINAL.json
└── teacher_dashboard_service.py

data/
├── before_after_improvement_FINAL.csv
├── concepts_final.csv
├── final_question_bank_270.csv
├── learning_content_FINAL.csv
├── personalized_learning_path_FINAL.csv
├── practice_questions_FINAL.csv
├── priority_profile_FINAL.csv
├── progress_summary_FINAL.json
└── smart_knowledge_gap.db

models/
├── ml_config_FINAL.json
├── ml_metrics_FINAL.json
└── ml_model_FINAL.joblib

static/
└── style.css

templates/
├── assessment.html
├── base.html
├── index.html
├── results.html
├── student_dashboard.html
└── teacher_dashboard.html

.gitignore
README.md
requirements.txt

## Installation

Install the dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Configuration

The application requires a `SECRET_KEY` environment variable.

Example:

```bash
export SECRET_KEY="your-secure-secret-key"
```

Do not commit real secrets to source control.

## Running the Application

From the project directory:

```bash
cd app
python app.py
```

When started directly, the Flask application uses port `5000` and binds to `0.0.0.0`.

For hosted deployment, the platform manages the application port.

## Main Routes

| Route | Purpose |
|---|---|
| `/` | Landing page |
| `/register` | Student registration |
| `/assessment/<student_id>` | Diagnostic assessment |
| `/assessment/<student_id>/submit` | Assessment submission |
| `/dashboard/<student_id>` | Student dashboard |
| `/teacher-dashboard` | Teacher dashboard |

## Assessment Flow

1. Register as a student.
2. Select a subject.
3. Select an educational level.
4. Start the diagnostic assessment.
5. Complete the 30-question assessment.
6. Calculate concept-level mastery.
7. Detect knowledge gaps.
8. Calculate learning priorities.
9. Generate the prerequisite-aware learning path.
10. Study the recommended learning content.
11. Practice related questions.
12. Complete reassessment.
13. Compare before and after mastery.

## Validation

The system has been validated through controlled and end-to-end testing covering:

- Backend contract validation
- Python syntax validation
- Question bank integrity
- Concept coverage
- Subject and level consistency
- Knowledge graph integrity
- Diagnostic engine behavior
- Priority engine behavior
- Personalized learning path generation
- Database persistence
- Student dashboard integration
- Teacher dashboard integration
- Practice and reassessment flow
- Before/after improvement
- Student and teacher dashboard consistency
- Flask runtime and route integration
- Production data and contract consistency

### Assessment Validation

All 9 subject-and-level combinations were validated:

- Mathematics — Beginner
- Mathematics — Intermediate
- Mathematics — Advanced
- Physics — Beginner
- Physics — Intermediate
- Physics — Advanced
- Computer Science — Beginner
- Computer Science — Intermediate
- Computer Science — Advanced

Each combination contains exactly:

- 30 questions
- 5 concepts
- 6 question types
- One subject
- One educational level

No subject or educational level mixing was detected.

### Machine Learning Evaluation

The ML layer is evaluated using development data.

Reported metrics include:

- Accuracy
- Precision
- Recall
- F1-score

These results are development evaluation results based on synthetic data and should not be interpreted as evidence of real-world model performance.

## Deployment

The application is deployed as a Flask web application on Faable.

The deployment is connected to the GitHub repository and uses the `master` branch.

The hosted application uses the platform-managed `PORT` environment variable and the required `SECRET_KEY` environment variable.

The SQLite database is suitable for the current portfolio/demo deployment. Because hosted filesystems may be ephemeral, durable production persistence would require a managed database for a production-scale deployment.

## Design Principles

- Concept-level diagnosis rather than total-score-only diagnosis
- One subject and one educational level per diagnostic assessment
- Exactly 30 questions per selected subject and level
- Explicit prerequisite relationships
- Prerequisite-aware learning order
- Diagnosed mastery states
- Separation between core educational logic and supporting ML
- Independent subject learning paths
- Persistent application data model
- Reassessment-based improvement measurement
- Separation between runtime logic and development artifacts

## Limitations

- The ML evaluation uses synthetic development data.
- The current learning content is structured around the defined project dataset.
- The system has not been presented as a validated real-world educational intervention.
- SQLite is suitable for the current demo/portfolio deployment but is not recommended for a production-scale multi-user system.
- The current core runtime does not use the stored ML model directly.
- Authentication and production-grade role-based access control are not yet implemented.

## Future Improvements

- Add larger real-world educational datasets
- Expand the number of subjects and concepts
- Improve adaptive question selection
- Add richer and more diverse learning content
- Add authentication and production-grade role-based access control
- Add a managed production database
- Expand automated testing
- Evaluate the system with real student learning outcomes
- Improve analytics and longitudinal learning progress tracking

## License

This project is provided for educational and portfolio purposes.
