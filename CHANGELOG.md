# Changelog

All notable changes to the Smart Knowledge Gap & Personalized Learning System
are documented in this file.

The format is based on Keep a Changelog (https://keepachangelog.com/en/1.1.0/),
and this project adheres to Semantic Versioning (https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-17

### Added
- Complete question bank with 270 questions across 3 subjects
  (Mathematics, Physics, Computer Science).
- 45 concepts organized by 3 difficulty levels
  (Beginner, Intermediate, Advanced).
- 6 question types per concept:
  Understanding, Application, Reasoning, Problem Solving,
  Misconception Detection, Transfer.
- Concept-level diagnostic engine.
- Mastery classification (Strong, Adequate, Weak, Critical).
- Gap score calculation.
- Knowledge Graph with prerequisite awareness.
- Priority engine for learning focus ordering.
- Personalized learning path generation.
- Learning content delivery per concept.
- Practice mode with additional questions per concept.
- Reassessment workflow with before/after mastery comparison.
- Student dashboard with mastery visualization.
- Teacher dashboard with class-level analytics.
- Automatic database initialization (init_database.py).
- Deterministic option shuffling per question.
- Session-based option mapping persistence.

### Fixed
- Answer scoring bug caused by option shuffling keyed on
  SECRET_KEY. The mapping is now derived from a stable seed and
  stored in the Flask session so display-time and submit-time
  mappings always match.
- Database schema is now created automatically if missing.

### Security
- All Flask sessions are signed with a SECRET_KEY loaded from
  environment variables.
- SQLite connections enforce foreign key constraints.

## [Unreleased]

### Planned
- Modern UI redesign with animations.
- Dark mode support.
- Interactive charts on dashboards.
- Optional LLM-based explanation layer.
- Export results as PDF.
