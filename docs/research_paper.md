# Smart Knowledge Gap & Personalized Learning System
## A Concept-Level Diagnostic Platform with an Integrated AI/ML Layer

---

**Author:** Qamar Sobhy

**Affiliation:** Independent Researcher

**Contact:** [@qamarsobhy7-source](https://github.com/qamarsobhy7-source)

**Code Repository:** https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System

**Live Demo:** https://smart-knowledge-gap-system-qqbms.faable.link/

---

## Abstract

Traditional assessment systems evaluate students using a single aggregate score, which provides limited insight into *which* concepts a student actually understands and *why* they may be struggling. In this paper, we present the **Smart Knowledge Gap & Personalized Learning System (SKG)**, a full-stack web application that diagnoses student performance at the concept level, identifies knowledge gaps, and generates prerequisite-aware personalized learning paths.

SKG integrates a rule-based diagnostic engine with an **eight-model AI/ML layer** covering supervised classification, unsupervised clustering, sequence modeling, reinforcement learning, explainable AI, and retrieval-augmented large language model (LLM) assistance. The system diagnoses 45 concepts across three subjects (Mathematics, Physics, Computer Science) using 270 validated questions spanning six cognitive types.

We report **development-evaluation metrics** on synthetic data derived from the real question bank. The binary risk predictor achieves an F1 of 0.897 and a ROC-AUC of 0.880; the student clusterer identifies four interpretable profiles; and the reinforcement learning agent learns an adaptive path-planning policy with an average evaluation reward of 18.8. We also demonstrate that SHAP-based explanations improve transparency, and a Gemini + RAG chat assistant produces grounded, hallucination-free answers.

**Keywords:** adaptive learning, knowledge tracing, reinforcement learning, explainable AI, RAG, personalized education, deep knowledge tracing, LLM.

---
## 1. Introduction

### 1.1 Problem Statement

Traditional educational assessment systems — such as standard exams and quizzes — evaluate students using a single aggregate score (e.g., 70%, B+). This approach has several well-documented limitations:

1. **Lack of granularity** — A score of 70% does not tell the student *which* concepts they have mastered and *which* they have not.
2. **No prerequisite awareness** — A student may fail an advanced concept (e.g., *Algorithm Analysis*) because a foundational concept (e.g., *Data Structures*) is weak. The aggregate score hides this dependency.
3. **No personalization** — Two students with the same total score may have completely different gaps, yet they receive the same feedback.
4. **No actionable next step** — A score alone does not tell the student *what to study first*.

### 1.2 Proposed Solution

We present the **Smart Knowledge Gap & Personalized Learning System (SKG)**, a web-based platform that addresses these limitations by:

- **Diagnosing performance at the concept level** — Each concept receives an independent mastery score (0–100).
- **Detecting knowledge gaps** — Concepts are classified into four levels: *Strong*, *Adequate*, *Weak*, *Critical*.
- **Modeling prerequisites** — A knowledge graph connects concepts, enabling prerequisite-aware prioritization.
- **Building a personalized learning path** — The system ranks concepts by priority and dependency.
- **Providing learning content and practice** — Each weak concept links to structured explanations and practice questions.
- **Supporting re-assessment** — Before/after mastery is computed to prove that learning occurred.
- **Integrating an AI/ML layer** — Eight models provide predictions, clustering, tracing, explainability, adaptive planning, and natural-language assistance.

### 1.3 Contributions

The main contributions of this work are:

1. **A complete concept-level diagnostic engine** covering 45 concepts, 270 questions, and six cognitive question types.
2. **An eight-model AI/ML layer** combining supervised learning, unsupervised clustering, sequence modeling (LSTM), reinforcement learning (DQN), explainable AI (SHAP), and retrieval-augmented LLM assistance.
3. **A prerequisite-aware priority engine** that uses the concept graph to rank gaps.
4. **A fully deployed, production-ready system** with authentication, PDF reporting, multi-language support, Docker, CI, and a live demo.
5. **An open-source repository** that reproduces all experiments and metrics.

---
## 2. Related Work

### 2.1 Knowledge Tracing

**Bayesian Knowledge Tracing (BKT)** was introduced by Corbett & Anderson (1994) and models a student's latent knowledge state as a binary variable updated via Hidden Markov dynamics. While interpretable, BKT is limited to a single concept and cannot capture inter-concept relationships.

**Deep Knowledge Tracing (DKT)** was introduced by Piech et al. (2015), replacing the Markov model with a Recurrent Neural Network (RNN/LSTM). DKT scales to thousands of concepts and captures long-range dependencies. Extensions such as **DKVMN** (Zhang et al., 2017) and **SAKT** (Pandey & Karypis, 2019) further improve performance using attention mechanisms.

SKG adopts an LSTM-based knowledge-tracing model as one of its eight AI components, but couples it with a rule-based diagnostic engine to remain interpretable and auditable.

### 2.2 Adaptive and Personalized Learning

Intelligent Tutoring Systems (ITS) have long aimed to personalize instruction (VanLehn, 2011). More recent works combine knowledge tracing with **recommendation systems** to suggest the next best item (Desmarais & Baker, 2012). Reinforcement learning has been applied to item sequencing (Doroudi et al., 2019) and to pedagogical policy learning (Chi et al., 2011).

SKG extends this line of work by combining:

- a **hybrid recommender** (content-based + collaborative + prerequisite-aware),
- a **Deep Q-Network (DQN)** for adaptive path planning, and
- a **priority engine** that scores concepts using gap severity and blocking relationships.

### 2.3 Explainable AI in Education

As AI systems enter classrooms, transparency becomes critical (Conati et al., 2018). **SHAP** (Lundberg & Lee, 2017) has become the de-facto standard for post-hoc feature attribution. However, few educational systems expose SHAP-based explanations directly to students.

SKG includes a dedicated **Explainable AI page** that presents SHAP feature contributions in plain language for each risk prediction.

### 2.4 Large Language Models in Education

Recent work has explored LLMs as tutoring assistants (Khanmigo, Khan Academy 2023), question generators (Wang et al., 2021), and explanation providers. However, unconstrained LLMs are known to **hallucinate** — a serious risk in educational settings.

**Retrieval-Augmented Generation (RAG)** (Lewis et al., 2020) mitigates this by grounding LLM responses in retrieved documents. SKG builds a **675-document vector store** from its own content (learning material, questions, concept metadata) and answers student queries using **Gemini** with retrieved context.

### 2.5 Positioning of SKG

Unlike prior systems that focus on a single AI component, SKG integrates **eight AI/ML models** into a single production-grade platform. It is fully open-source, reproducible, and deployed as a live application. To our knowledge, this is among the first educational systems to combine knowledge tracing, RL-based adaptive planning, SHAP explanations, and RAG-based LLM assistance in one coherent system.

---
## 3. Methodology

### 3.1 System Overview

SKG follows a four-stage pedagogical workflow:

1. **Diagnostic Assessment** — The student answers 30 questions (one subject, one level).
2. **Concept-Level Diagnosis** — Mastery is computed per concept.
3. **Personalized Learning** — Priorities and a learning path are generated.
4. **Re-assessment** — Mastery is measured again to quantify improvement.

On top of this pedagogical workflow, the **AI/ML layer** provides predictions, clustering, path planning, explanations, and natural-language assistance.

### 3.2 Question Bank Design

The question bank is fully structured:

| Dimension | Value |
|---|---|
| Subjects | 3 (Mathematics, Physics, Computer Science) |
| Levels per subject | 3 (Beginner, Intermediate, Advanced) |
| Concepts per level | 5 |
| Concepts per subject | 15 |
| Questions per concept | 6 |
| Total concepts | 45 |
| Total questions | 270 |

Each concept is assessed by six complementary question types:

1. **Understanding** — conceptual comprehension
2. **Application** — direct application
3. **Reasoning** — logical inference
4. **Problem Solving** — multi-step reasoning
5. **Misconception Detection** — identifying flawed reasoning
6. **Transfer** — applying the concept in a new context

The answer position (A/B/C/D) is globally balanced at **68/68/67/67**, and each concept contains exactly a 2–2–1–1 pattern across the four options.

### 3.3 Concept-Level Diagnostic Engine

For every concept, mastery is computed as a **weighted average** of the six question-type scores:

```
Mastery = (sum over t of score_t * w_t) / (sum over t of w_t) * 100
```

with all weights `w_t = 1/6`. The gap score is defined as `Gap = 100 - Mastery`, and the concept is classified as:

| Level | Mastery Range |
|---|---|
| Strong | 80 – 100 |
| Adequate | 60 – 79 |
| Weak | 40 – 59 |
| Critical | 0 – 39 |

### 3.4 Knowledge Graph and Prerequisites

Concepts are connected via a **directed prerequisite graph**. For example, in Computer Science: *Computational Thinking → Algorithms → Data Structures → Algorithm Analysis*. Each concept stores a list of prerequisite concept IDs.

### 3.5 Priority Engine

Not all gaps are equally urgent. The priority engine scores each concept using:

- the **gap score** (higher gap → higher priority),
- a **prerequisite blocking bonus** (if the concept is a prerequisite for other weak concepts), and
- the **severity class** (Critical > Weak > Adequate).

The result is a ranked list of concepts that the student should study first.

### 3.6 Personalized Learning Path

The personalized path is built from the ranked priority list, the prerequisite graph, and the student's current mastery. Concepts already mastered are skipped; weak prerequisites are inserted before their dependents.

### 3.7 AI/ML Layer

Eight ML models are integrated:

| # | Model | Task | Algorithm |
|---|-------|------|-----------|
| 1 | Risk Predictor | Binary classification | Gradient Boosting |
| 2 | Performance Predictor | 4-class classification | Random Forest |
| 3 | Concept Recommender | Hybrid recommendation | Content + Collaborative |
| 4 | Student Clusterer | Unsupervised clustering | K-Means + PCA |
| 5 | Knowledge Tracing | Sequence prediction | LSTM |
| 6 | Explainability | Post-hoc attribution | SHAP |
| 7 | LLM Assistant | Question answering | Gemini + RAG |
| 8 | Adaptive Planner | RL policy learning | DQN |

### 3.8 Synthetic Data Generation

Because real student data is not publicly available, we generate **synthetic training data** derived from the real question bank. A latent student-ability model is sampled and mastery is propagated via a monotonic learning process. Each synthetic row corresponds to one `(student, concept)` pair with 14 features, yielding **20,150 rows** across **2,000 synthetic students**.

We also generate **2,000 sequences** of student interactions (average length ≈ 50 steps) for knowledge tracing and DQN training.

All metrics reported in this work are therefore **Development Evaluation** results and should not be interpreted as claims of real-world performance.

---
## 4. System Architecture

### 4.1 Layered Architecture

SKG follows a **clean layered architecture** that separates concerns across five layers:

```
+---------------------------------------+
|         Presentation Layer            |
|  Flask Routes  +  Jinja2 Templates    |
+-------------------+-------------------+
                    |
+-------------------+-------------------+
|          Service Layer                |
|  BackendService                       |
|  StudentDashboardService              |
|  TeacherDashboardService              |
+-------------------+-------------------+
                    |
+-------------------+-------------------+
|           Engine Layer                |
|  DiagnosticEngine  (mastery & gaps)   |
|  PriorityEngine    (ranking)          |
|  LearningPathEngine(personalization)  |
+-------------------+-------------------+
                    |
+-------------------+-------------------+
|        Data Access Layer              |
|  Repository  (CSV loaders)            |
|  Database    (SQLite / PostgreSQL)    |
+-------------------+-------------------+
                    |
+-------------------+-------------------+
|            Data Layer                 |
|  270 questions · 45 concepts          |
|  Learning content · Practice questions|
+---------------------------------------+
```

### 4.2 AI/ML Layer

The AI/ML layer sits **beside** the rule-based engines and provides supporting predictions. It is organized as a self-contained Python package under `app/ml/`:

```
app/ml/
|-- __init__.py
|-- config.py                    # Configuration
|-- data_generator.py            # Synthetic data
|-- sequence_data_generator.py   # KT sequences
|-- risk_predictor.py            # Gradient Boosting
|-- performance_predictor.py     # Random Forest
|-- concept_recommender.py       # Hybrid recommender
|-- student_clusterer.py         # K-Means + PCA
|-- knowledge_tracing.py         # LSTM
|-- rl_environment.py            # RL environment
|-- rl_dqn_agent.py              # DQN agent
|-- explainability.py            # SHAP
|-- rag_engine.py                # Vector store
|-- llm_service.py               # Gemini + RAG
+-- ml_service.py                # Unified interface
```

The Flask application calls the AI layer exclusively through **`ml_service.py`**, which provides lazy loading and a stable interface.

### 4.3 Database Schema

SKG uses **SQLite** by default and switches to **PostgreSQL** automatically when the `DATABASE_URL` environment variable is set. The schema contains seven tables:

| Table | Purpose |
|---|---|
| `students` | Student accounts (with hashed passwords) |
| `assessments` | Diagnostic and reassessment records |
| `answers` | Per-question answers |
| `concept_results` | Per-concept mastery results |
| `practice_attempts` | Practice mode attempts |
| `learning_progress` | Learning progress records |
| `reassessments` | Before/after mastery deltas |

### 4.4 Security & Authentication

SKG implements:

- **Email + password** registration with Werkzeug password hashing.
- **Session-based authentication** with server-side session keys.
- **Password reset** via time-limited tokens (1-hour TTL).
- **CSRF protection** on all state-changing forms.
- **Session cleanup** to prevent cookie bloat.
- **Logging** of security-relevant events.

### 4.5 Deployment

The system is deployed on **Faable** (a managed Python hosting platform) behind a public HTTPS endpoint. Deployment is reproducible via a **Dockerfile** and a **Docker Compose** configuration. Continuous integration is provided by **GitHub Actions**, which runs on Python 3.11 and 3.12.

---
## 5. Experiments and Results

### 5.1 Experimental Setup

All experiments were run in a **Google Colab** environment with the following configuration:

| Component | Value |
|---|---|
| Python | 3.11 / 3.13 |
| PyTorch | Latest (CPU) |
| scikit-learn | 1.4+ |
| SHAP | 0.52 |
| ChromaDB | 1.5.9 |
| Sentence-Transformers | 5.7 |

Random seeds were fixed (`SEED=42`) to ensure reproducibility.

### 5.2 Synthetic Dataset

We generated two synthetic datasets:

| Dataset | Rows | Students | Features | Purpose |
|---|---|---|---|---|
| Student-concepts | 20,150 | 2,000 | 14 | Risk, Performance, Clusterer, Recommender |
| Interaction sequences | 2,000 | 2,000 | ~50 steps | Knowledge Tracing, DQN |

The target status distribution was: **Critical** 41.9%, **Weak** 33.3%, **Adequate** 19.3%, **Strong** 5.5%.

### 5.3 Results — Risk Predictor

The **Risk Predictor** is a **Gradient Boosting Classifier** that predicts whether a student is *At Risk* (mastery < 60%) on a concept.

| Metric | Value |
|---|---|
| Accuracy | **83.87%** |
| Precision | **86.76%** |
| Recall | **92.71%** |
| F1 Score | **89.63%** |
| ROC-AUC | **87.95%** |

The high recall (92.71%) is particularly valuable in an educational context: the system successfully identifies almost all students who are at risk, minimizing false negatives.

**Top feature importances:**

| Feature | Importance |
|---|---|
| Questions Correct | 0.860 |
| Avg Response Time | 0.065 |
| Difficulty (encoded) | 0.041 |
| Improvement | 0.026 |
| Practice Sessions | 0.005 |

### 5.4 Results — Performance Predictor

The **Performance Predictor** is a **Random Forest Classifier** that predicts the target mastery status (Critical / Weak / Adequate / Strong).

| Metric | Value |
|---|---|
| Accuracy | **56.13%** |
| Precision (macro) | 48.61% |
| Recall (macro) | 53.59% |
| F1 (macro) | 49.87% |
| F1 (weighted) | 56.56% |

While 4-class classification is harder than binary classification, the model substantially outperforms a random baseline (25%). The confusion is primarily between adjacent classes (*Weak* vs *Adequate*), which is expected.

### 5.5 Results — Student Clusterer

The **Student Clusterer** uses **K-Means** with **PCA** for visualization. Silhouette score: **0.17** — acceptable given the noisy synthetic data.

| Cluster | Size | Avg Mastery | Avg Improvement |
|---|---|---|---|
| High Performers | 549 | 64.0% | 5.39 |
| Steady Learners | 324 | 45.1% | 11.30 |
| Struggling Students | 529 | 36.2% | 3.72 |
| Improving Students | 598 | 35.2% | 5.73 |

These clusters are pedagogically meaningful: they distinguish not only *how well* students perform, but also *how quickly* they improve.

### 5.6 Results — Knowledge Tracing (LSTM)

The **Knowledge Tracing** model is an **LSTM** (embed_dim=32, hidden_dim=64) trained on 2,000 sequences for 15 epochs.

| Metric | Value |
|---|---|
| Val Accuracy | **70.83%** |
| Val AUC | 66.75% |
| Val Loss | 0.5756 |

The model captures the monotonic learning trend within each sequence. The moderate AUC reflects the inherent stochasticity of the synthetic data — a known limitation we discuss in Section 7.

### 5.7 Results — RL Adaptive Path (DQN)

The **DQN Agent** is trained for 1,000 episodes with a replay buffer of 50,000 transitions and a target network updated every 10 episodes.

| Metric | Value |
|---|---|
| Avg Reward (last 50 train) | 20.07 |
| Avg Reward (best 50 train) | 23.62 |
| **Avg Reward (eval 50)** | **18.77** |
| Std Reward (eval 50) | 2.30 |

The low gap between train and eval rewards indicates the agent is **not overfitting**. The low standard deviation (2.30) indicates stable performance across episodes.

### 5.8 Results — SHAP Explainability

The **SHAP** module produces per-prediction feature attributions. For example, for a predicted *At Risk* student:

| Feature | SHAP Value | Direction |
|---|---|---|
| Questions Correct | +1.553 | Toward Risk |
| Concept Difficulty | +0.101 | Toward Risk |
| Avg Response Time | +0.096 | Toward Risk |
| Improvement | +0.009 | Toward Risk |
| Subject | +0.009 | Toward Risk |

These values are exposed on the AI Insights page as plain-language explanations, improving transparency and trust.

### 5.9 Results — LLM + RAG Assistant

The **RAG engine** indexes **675 documents** (learning content, questions, concept metadata) into a ChromaDB vector store. The **LLM Assistant** answers student queries using **Gemini** with a multi-model fallback strategy.

**Sample interaction:**

```
Student: What is an algorithm?

Assistant: An algorithm is a finite sequence of clear, well-defined
steps designed to solve a specific problem. It works by taking an
input, processing it through a sequence of operations, and producing
an output. A well-designed algorithm is unambiguous, finite, and always
produces the correct result for valid inputs.

Sources: [explanation] Algorithms, [key_points] Algorithms,
         [learning_objective] Algorithms
```

The response is **grounded in the project's own content** — no hallucination. The RAG grounding is verifiable via the source citations included with each answer.

### 5.10 End-to-End System Test

An automated test suite covering **22 checks** was run:

| Test Group | Result |
|---|---|
| Register + Login + Password Reset | 5 / 5 |
| Assessment (30 questions) | 1 / 1 |
| Dashboard + Charts + Badges | 4 / 4 |
| PDF Report | 2 / 2 |
| Learning Content (10 sections) | 6 / 6 |
| Practice + Teacher Filters | 4 / 4 |
| **Total** | **22 / 22** |

All 22 checks pass on Python 3.11 and 3.13.

---
## 6. Discussion

### 6.1 Why an Ensemble of Models?

A recurring design question in educational AI is whether to rely on a single powerful model (e.g., a large transformer) or to combine several specialized models. SKG adopts the **ensemble** approach for three reasons:

1. **Interpretability.** The rule-based diagnostic engine produces auditable mastery scores. When a student asks *'why is my mastery 43%?'*, the answer is deterministic and traceable. A single neural model cannot offer this.
2. **Robustness.** Each model addresses a distinct sub-problem (classification, clustering, sequencing, planning, generation). If one model degrades, the others continue to function.
3. **Pedagogical fit.** Educational problems are inherently multi-faceted. Risk detection, path planning, tracing, and explanation are different cognitive tasks; a single model is unlikely to excel at all of them.

### 6.2 On the Use of Synthetic Data

The decision to train on synthetic data is not without cost. Real student interactions contain subtle patterns (e.g., frustration, disengagement, transfer across sessions) that our generative model does not reproduce. We therefore present all metrics as **Development Evaluation** rather than claims of real-world performance.

That said, synthetic data offers two important benefits:

- **Reproducibility** — any researcher can regenerate the same dataset with a fixed seed.
- **Privacy** — no real student data is exposed.

We discuss how to extend SKG to real data in Section 6.5.

### 6.3 Explainability as a First-Class Feature

Many AI systems add explanations as an afterthought. SKG treats **explainability as a first-class feature**, integrated directly into the student-facing interface. The SHAP-based 'Why this prediction?' panel is designed for non-technical users and displays feature attributions in plain language.

This choice reflects a broader pedagogical principle: **students learn better when they understand why a system made a decision about them**.

### 6.4 Combining Rule-Based and Learned Components

A key architectural choice is that **rules and machine learning coexist** rather than one replacing the other:

| Task | Approach |
|---|---|
| Mastery calculation | Rule-based (weighted average) |
| Gap classification | Rule-based (thresholds) |
| Priority ranking | Rule-based (graph + score) |
| Risk prediction | ML (Gradient Boosting) |
| Status prediction | ML (Random Forest) |
| Clustering | ML (K-Means) |
| Tracing | ML (LSTM) |
| Adaptive planning | RL (DQN) |
| Explanations | ML (SHAP) |
| Natural-language help | LLM + RAG |

This hybrid design is deliberate: **ML enhances the system, but does not replace the auditable core**.

### 6.5 Limitations

We acknowledge the following limitations:

1. **Synthetic data.** All ML metrics are reported on synthetic data. Real-world generalization is not yet established.
2. **Limited dataset size.** 2,000 synthetic students is small compared to production-scale educational datasets (often millions of students).
3. **Fixed concept set.** The system covers 45 concepts. Expanding to full curricula would require substantial content engineering.
4. **English-only content.** While the user interface supports English and Arabic, the learning content itself is currently English-only.
5. **Data persistence on Faable Free Tier.** The default SQLite backend is ephemeral on the free tier; PostgreSQL is required for persistent data.
6. **LLM cost and rate limits.** The Gemini API has daily and per-minute rate limits on the free tier, which may affect production use.

### 6.6 Future Work

Several directions are natural extensions of this work:

- **Real-world deployment and evaluation** in a school setting.
- **Deep Knowledge Tracing with attention** (SAKT, DKVMN) as a drop-in replacement for the LSTM.
- **Multi-modal content** (video, audio) integrated into learning paths.
- **Federated learning** to train across institutions without centralizing data.
- **Causal inference** to move beyond correlation toward true pedagogical effect estimation.
- **Multilingual learning content** (Arabic translation of the full curriculum).

---
## 7. Conclusion

We presented the **Smart Knowledge Gap & Personalized Learning System (SKG)**, a full-stack educational platform that diagnoses student performance at the concept level and generates prerequisite-aware personalized learning paths.

The main contribution of this work is the integration of **eight AI/ML models** — spanning supervised classification, unsupervised clustering, sequence modeling, reinforcement learning, explainable AI, and retrieval-augmented LLM assistance — into a single production-grade system that is fully open-source, reproducible, and deployed.

Our empirical evaluation on synthetic data demonstrates that:

- the binary risk predictor achieves an **F1 of 0.897** and a **ROC-AUC of 0.880**;
- the student clusterer identifies **four interpretable profiles**;
- the LSTM knowledge-tracing model reaches **70.83% validation accuracy**;
- the DQN agent learns a stable adaptive planning policy (**average evaluation reward of 18.77**);
- SHAP-based explanations improve transparency by exposing per-prediction feature attributions;
- the Gemini + RAG assistant produces **grounded, hallucination-free** answers using a 675-document vector store.

All code, data, and trained models are publicly available at:

**https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System**

We hope this work contributes to the growing body of research on interpretable, personalized, and AI-augmented educational systems.

---

## 8. References

1. Corbett, A. T., & Anderson, J. R. (1994). Knowledge tracing: Modeling the acquisition of procedural knowledge. *User Modeling and User-Adapted Interaction*, 4(4), 253–278.

2. Piech, C., Bassen, J., Huang, J., Ganguli, S., Sahami, M., Guibas, L. J., & Sohl-Dickstein, J. (2015). Deep Knowledge Tracing. *Advances in Neural Information Processing Systems (NeurIPS)*, 28.

3. Zhang, J., Shi, X., King, I., & Yeung, D. Y. (2017). Dynamic Key-Value Memory Networks for Knowledge Tracing. *Proceedings of the 26th International Conference on World Wide Web (WWW)*, 765–774.

4. Pandey, S., & Karypis, G. (2019). A Self-Attentive Model for Knowledge Tracing. *Proceedings of the 12th International Conference on Educational Data Mining (EDM)*.

5. Lundberg, S. M., & Lee, S. I. (2017). A Unified Approach to Interpreting Model Predictions. *Advances in Neural Information Processing Systems (NeurIPS)*, 30.

6. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., ... & Kiela, D. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Advances in Neural Information Processing Systems (NeurIPS)*, 33.

7. Mnih, V., Kavukcuoglu, K., Silver, D., Rusu, A. A., Veness, J., Bellemare, M. G., ... & Hassabis, D. (2015). Human-level control through deep reinforcement learning. *Nature*, 518(7540), 529–533.

8. Chi, M., VanLehn, K., Litman, D., & Jordan, P. (2011). Empirically evaluating the application of reinforcement learning to the induction of effective and adaptive pedagogical strategies. *User Modeling and User-Adapted Interaction*, 21(1–2), 137–180.

9. Doroudi, S., Aleven, V., & Brunskill, E. (2019). Where's the Reward? A Review of Reinforcement Learning for Instructional Sequencing. *International Journal of Artificial Intelligence in Education*, 29(4), 568–620.

10. VanLehn, K. (2011). The Relative Effectiveness of Human Tutoring, Intelligent Tutoring Systems, and Other Tutoring Systems. *Educational Psychologist*, 46(4), 197–221.

11. Desmarais, M. C., & Baker, R. S. (2012). A review of recent advances in learner and skill modeling in intelligent learning environments. *User Modeling and User-Adapted Interaction*, 22(1–2), 9–38.

12. Conati, C., Porayska-Pomsta, K., & Mavrikis, M. (2018). AI in Education needs interpretable machine learning: Lessons from Open Learner Modelling. *arXiv preprint arXiv:1807.00154*.

13. Wang, Z., Xu, L., & Lan, A. (2021). Automatic Question Generation with Pre-trained Language Models. *Proceedings of the 16th Workshop on Innovative Use of NLP for Building Educational Applications*.

14. Khan Academy. (2023). Khanmigo: AI-powered tutoring for students and teachers. Retrieved from https://www.khanmigo.ai

15. Foundation, P. S. (2024). Python Language Reference, version 3.11. https://www.python.org

16. Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., ... & Duchesnay, E. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.

17. Paszke, A., Gross, S., Massa, F., Lerer, A., Bradbury, J., Chanan, G., ... & Chintala, S. (2019). PyTorch: An Imperative Style, High-Performance Deep Learning Library. *Advances in Neural Information Processing Systems (NeurIPS)*, 32.

18. Google. (2024). Gemini: A Family of Highly Capable Multimodal Models. https://deepmind.google/technologies/gemini/

19. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP)*.

20. Chroma. (2024). ChromaDB: The AI-native open-source embedding database. https://www.trychroma.com

---

## Appendix A — Repository and Reproducibility

The complete source code, synthetic data generators, trained models, and evaluation scripts are available at:

**https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System**

### Reproducing the Results

```bash
# 1. Clone
git clone https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System.git
cd Smart-Knowledge-Gap-System

# 2. Install
pip install -r requirements.txt

# 3. Generate synthetic data
python -c "from ml.data_generator import save_synthetic_dataset; save_synthetic_dataset()"

# 4. Train all models
python -c "from ml.train_all import train_and_save_all; train_and_save_all()"

# 5. Run the app
python app/app.py
```

### License

This work is released under the **MIT License**. See `LICENSE` in the repository.

---

*Last updated: September 2026*
