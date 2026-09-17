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

### 📈 Before vs After Improvement

After completing the learning path, the student takes a **re-assessment**. The system then computes:

<!-- Force redeploy: 2026-09-17 19:34:58 -->
