"""
Database initialization module.

Creates all required tables for the Smart Knowledge Gap System
if they do not already exist.

Usage:
    python -m app.init_database
or:
    from init_database import initialize_database
    initialize_database()
"""

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "smart_knowledge_gap.db"


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-- ============================================================
-- STUDENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS students (
    student_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name               TEXT    NOT NULL,
    email                   TEXT    UNIQUE,
    password_hash           TEXT,
    password_reset_token    TEXT,
    password_reset_expires  TIMESTAMP,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_students_email
    ON students(email);

-- ============================================================
-- ASSESSMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    assessment_type TEXT    NOT NULL CHECK (
        assessment_type IN ('Diagnostic', 'Reassessment')
    ),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assessments_student
    ON assessments(student_id);

CREATE INDEX IF NOT EXISTS idx_assessments_type
    ON assessments(assessment_type);

-- ============================================================
-- ANSWERS
-- ============================================================
CREATE TABLE IF NOT EXISTS answers (
    answer_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id  INTEGER NOT NULL,
    question_id    TEXT    NOT NULL,
    student_answer TEXT    NOT NULL,
    is_correct     INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
    score          REAL    NOT NULL CHECK (score >= 0.0 AND score <= 100.0),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        ON DELETE CASCADE,
    UNIQUE (assessment_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_answers_assessment
    ON answers(assessment_id);

CREATE INDEX IF NOT EXISTS idx_answers_question
    ON answers(question_id);

-- ============================================================
-- CONCEPT RESULTS
-- ============================================================
CREATE TABLE IF NOT EXISTS concept_results (
    result_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    concept_id    INTEGER NOT NULL,
    mastery       REAL    NOT NULL CHECK (mastery >= 0.0 AND mastery <= 100.0),
    gap_level     TEXT    NOT NULL,
    gap_score     REAL    NOT NULL CHECK (gap_score >= 0.0 AND gap_score <= 100.0),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        ON DELETE CASCADE,
    UNIQUE (assessment_id, concept_id)
);

CREATE INDEX IF NOT EXISTS idx_concept_results_assessment
    ON concept_results(assessment_id);

CREATE INDEX IF NOT EXISTS idx_concept_results_concept
    ON concept_results(concept_id);

-- ============================================================
-- LEARNING PROGRESS
-- ============================================================
CREATE TABLE IF NOT EXISTS learning_progress (
    progress_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id    INTEGER NOT NULL,
    concept_id    INTEGER NOT NULL,
    learning_step INTEGER NOT NULL,
    status        TEXT    NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_learning_progress_student
    ON learning_progress(student_id);

-- ============================================================
-- PRACTICE ATTEMPTS
-- ============================================================
CREATE TABLE IF NOT EXISTS practice_attempts (
    attempt_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER NOT NULL,
    question_id    TEXT    NOT NULL,
    student_answer TEXT    NOT NULL,
    is_correct     INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
    score          REAL    NOT NULL CHECK (score >= 0.0 AND score <= 100.0),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_practice_attempts_student
    ON practice_attempts(student_id);

CREATE INDEX IF NOT EXISTS idx_practice_attempts_question
    ON practice_attempts(question_id);

-- ============================================================
-- REASSESSMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS reassessments (
    reassessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    concept_id      INTEGER NOT NULL,
    before_mastery  REAL    NOT NULL CHECK (before_mastery >= 0.0 AND before_mastery <= 100.0),
    after_mastery   REAL    NOT NULL CHECK (after_mastery >= 0.0 AND after_mastery <= 100.0),
    improvement     REAL    NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reassessments_student
    ON reassessments(student_id);

CREATE INDEX IF NOT EXISTS idx_reassessments_concept
    ON reassessments(concept_id);
"""


def initialize_database(db_path=None, verbose=True):
    """
    Create all required tables if they do not exist.

    Args:
        db_path: Optional custom path to the SQLite database file.
        verbose: Print progress messages.

    Returns:
        Path to the initialized database file.
    """

    if db_path is None:
        db_path = DB_PATH
    else:
        db_path = Path(db_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"📂 Database path: {db_path}")

    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_SQL)
        connection.commit()

        cursor = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        if verbose:
            print(f"✅ Database initialized successfully.")
            print(f"📋 Tables: {', '.join(tables)}")

        return db_path
    finally:
        connection.close()


def database_exists(db_path=None):
    """Return True if the database file exists and has tables."""
    if db_path is None:
        db_path = DB_PATH
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        return False

    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type='table' AND name='students'"
        )
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        connection.close()


def migrate_existing_database(db_path=None, verbose=True):
    """
    Add new columns to an existing database if they don't exist.

    Currently handles:
        - students.password_reset_token
        - students.password_reset_expires
    """
    if db_path is None:
        db_path = DB_PATH
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        return False

    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()

        # Get existing columns
        cursor.execute("PRAGMA table_info(students)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        added = []

        if "password_reset_token" not in existing_cols:
            cursor.execute(
                "ALTER TABLE students ADD COLUMN password_reset_token TEXT"
            )
            added.append("password_reset_token")

        if "password_reset_expires" not in existing_cols:
            cursor.execute(
                "ALTER TABLE students ADD COLUMN password_reset_expires TIMESTAMP"
            )
            added.append("password_reset_expires")

        connection.commit()

        if verbose and added:
            print(f"✅ Migrated DB: added columns {added}")

        return len(added) > 0
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    migrate_existing_database()
