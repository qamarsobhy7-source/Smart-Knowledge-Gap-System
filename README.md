# Smart Knowledge Gap & Personalized Learning System

A web-based personalized learning system that analyzes student performance at the concept level, identifies knowledge gaps, prioritizes learning needs, and generates prerequisite-aware personalized learning paths.

The system is designed for three academic subjects:

- Mathematics
- Physics
- Computer Science

## Overview

Traditional assessment systems often rely mainly on total scores. This project focuses on concept-level learning analysis.

The system evaluates student answers across individual concepts and determines:

- Which concepts are strong
- Which concepts require improvement
- Which concepts are critical knowledge gaps
- Which concepts should be prioritized first
- Which prerequisite concepts should be learned before dependent concepts
- How learning performance changes after reassessment

The learning workflow is:

**Student → Diagnostic Assessment → Concept-Level Analysis → Mastery & Knowledge Gaps → Knowledge Graph → Priority Calculation → Personalized Learning Path → Learning Content & Practice → Re-assessment → Improvement Analysis**

## System Scope

The current system contains:

- 3 subjects
- 3 difficulty levels per subject
- 45 concepts
- 270 diagnostic questions
- 6 questions per concept
- 6 question types per concept

The six question types are:

1. Understanding
2. Application
3. Reasoning
4. Problem Solving
5. Misconception Detection
6. Transfer

## Core Components

### 1. Diagnostic Assessment

The diagnostic engine processes student answers and calculates concept-level mastery instead of relying only on an overall score.

Each concept is evaluated independently so that a student can demonstrate strong performance in some concepts while having gaps in others.

### 2. Knowledge Gap Detection

The system classifies concept mastery and identifies learning gaps.

Knowledge gaps are analyzed at the concept level and can be affected by prerequisite relationships in the knowledge graph.

### 3. Knowledge Graph

The system contains prerequisite relationships between concepts.

The knowledge graph helps determine the correct learning order and prevents students from being directed toward advanced concepts before required prerequisite concepts.

### 4. Priority Engine

Learning priorities are calculated using the diagnosed concept state and prerequisite relationships.

This allows the system to determine which concepts should receive attention first.

### 5. Personalized Learning Path

The learning path is generated from the student's identified learning targets.

The path is prerequisite-aware and produces an ordered sequence of learning targets for each subject.

### 6. Learning Content and Practice

Each concept is connected to learning content and practice questions.

The practice bank contains 270 questions with six question types for every concept.

### 7. Re-assessment and Improvement

After learning, students can be reassessed.

The system compares before and after mastery values to calculate learning improvement.

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
- Concept-level performance
- Knowledge gaps
- Learning priorities
- Learning progress
- Practice activity
- Reassessment and improvement

## Supporting Machine Learning Layer

The project also includes a machine learning prediction layer.

ML is intentionally implemented as a **supporting layer**, not as the sole authority for diagnosis.

The current application runtime does not depend on the ML model for its core diagnostic workflow.

The stored ML artifacts include:

- Development dataset
- Trained model
- Prediction results
- Evaluation metrics
- ML configuration

The current ML evaluation is classified as **Development Evaluation**.

The development dataset is synthetic and is intended for system development and evaluation. The reported metrics must not be interpreted as real-world educational performance.

## Data

The production data layer contains:

- 270-question final question bank
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

The project contains offline/supporting ML artifacts. These artifacts are not required by the core application runtime.

## Project Structure

```text
Smart_Knowledge_Gap_System_PRODUCTION/
├── app/
│   ├── app.py
│   ├── backend_contract_FINAL.json
│   ├── backend_service.py
│   ├── database.py
│   ├── diagnostic_engine.py
│   ├── learning_path_engine.py
│   ├── priority_engine.py
│   ├── repository.py
│   ├── student_dashboard_contract_FINAL.json
│   ├── student_dashboard_service.py
│   ├── teacher_dashboard_contract_FINAL.json
│   └── teacher_dashboard_service.py
├── data/
│   ├── concepts_final.csv
│   ├── final_question_bank_270.csv
│   ├── learning_content_FINAL.csv
│   ├── personalized_learning_path_FINAL.csv
│   ├── practice_questions_FINAL.csv
│   ├── priority_profile_FINAL.csv
│   ├── before_after_improvement_FINAL.csv
│   ├── progress_summary_FINAL.json
│   └── smart_knowledge_gap.db
├── models/
│   ├── ml_config_FINAL.json
│   ├── ml_metrics_FINAL.json
│   └── ml_model_FINAL.joblib
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── assessment.html
│   ├── results.html
│   ├── student_dashboard.html
│   └── teacher_dashboard.html
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

Use Python 3.13 or a compatible Python environment.

Install the runtime dependencies:

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

The application uses port 5000 and binds to `0.0.0.0` when started directly.

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
2. Start the diagnostic assessment.
3. Submit answers.
4. Analyze concept-level mastery.
5. Detect knowledge gaps.
6. Calculate learning priorities.
7. Generate the personalized learning path.
8. Study the recommended learning content.
9. Practice related questions.
10. Complete reassessment.
11. Compare before and after mastery.

## Evaluation

### System and Runtime Evaluation

The application has been validated through end-to-end runtime testing covering:

- Student registration
- Diagnostic assessment
- Full 270-question submission
- Results generation
- Student dashboard
- Teacher dashboard
- Database persistence
- Empty production database state
- Route and template integration

### Machine Learning Evaluation

The ML layer is evaluated using development data.

Reported metrics include:

- Accuracy
- Precision
- Recall
- F1-score

These results are development evaluation results based on synthetic data and should not be interpreted as evidence of real-world model performance.

## Design Principles

- Concept-level diagnosis rather than total-score-only diagnosis
- Explicit prerequisite relationships
- Personalized learning order
- Separation between core educational logic and supporting ML
- Independent subject learning paths
- Persistent application data
- Reassessment-based improvement measurement
- Separation between production runtime and development artifacts

## Limitations

- The ML evaluation uses synthetic development data.
- The current learning content is structured around the defined project dataset.
- The system has not been presented as a validated real-world educational intervention.
- Production deployment configuration depends on the selected hosting platform.
- The current core runtime does not use the stored ML model directly.

## Future Improvements

- Add larger real-world educational datasets
- Expand the number of subjects and concepts
- Improve adaptive question selection
- Add richer learning content
- Add authentication and role-based access control
- Add production deployment configuration for a selected hosting platform
- Expand automated testing
- Evaluate the system with real student learning outcomes

## License

This project is provided for educational and portfolio purposes.
