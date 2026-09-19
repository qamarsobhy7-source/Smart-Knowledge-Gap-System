"""
Database initialization module.

Supports both SQLite (local dev) and PostgreSQL (production).

Usage:
    python -m app.init_database
or:
    from init_database import initialize_database
    initialize_database()
"""

import os
import sqlite3
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
IS_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "smart_knowledge_gap.db"


# ============================================================
# SCHEMA — SQLite
# ============================================================
SQLITE_SCHEMA = """
PRAGMA foreign_keys = ON;

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

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    assessment_type TEXT    NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assessments_student
    ON assessments(student_id);

CREATE TABLE IF NOT EXISTS answers (
    answer_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id  INTEGER NOT NULL,
    question_id    TEXT    NOT NULL,
    student_answer TEXT    NOT NULL,
    is_correct     INTEGER NOT NULL,
    score          REAL    NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_answers_assessment
    ON answers(assessment_id);

CREATE TABLE IF NOT EXISTS concept_results (
    result_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    concept_id    INTEGER NOT NULL,
    mastery       REAL    NOT NULL,
    gap_level     TEXT    NOT NULL,
    gap_score     REAL    NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        ON DELETE CASCADE
);

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

CREATE TABLE IF NOT EXISTS practice_attempts (
    attempt_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER NOT NULL,
    question_id    TEXT    NOT NULL,
    student_answer TEXT    NOT NULL,
    is_correct     INTEGER NOT NULL,
    score          REAL    NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reassessments (
    reassessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    concept_id      INTEGER NOT NULL,
    before_mastery  REAL    NOT NULL,
    after_mastery   REAL    NOT NULL,
    improvement     REAL    NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feynman_attempts (
    attempt_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER NOT NULL,
    concept_id     INTEGER NOT NULL,
    explanation    TEXT    NOT NULL,
    score          REAL    NOT NULL,
    feedback       TEXT,
    strengths      TEXT,
    gaps           TEXT,
    suggestions    TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feynman_student
    ON feynman_attempts(student_id);
"""


# ============================================================
# SCHEMA — PostgreSQL
# ============================================================
POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id              SERIAL PRIMARY KEY,
    full_name               TEXT    NOT NULL,
    email                   TEXT    UNIQUE,
    password_hash           TEXT,
    password_reset_token    TEXT,
    password_reset_expires  TIMESTAMP,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_students_email
    ON students(email);

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id   SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL,
    assessment_type TEXT    NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assessments_student
    ON assessments(student_id);

CREATE TABLE IF NOT EXISTS answers (
    answer_id      SERIAL PRIMARY KEY,
    assessment_id  INTEGER NOT NULL,
    question_id    TEXT    NOT NULL,
    student_answer TEXT    NOT NULL,
    is_correct     INTEGER NOT NULL,
    score          REAL    NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_answers_assessment
    ON answers(assessment_id);

CREATE TABLE IF NOT EXISTS concept_results (
    result_id     SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    concept_id    INTEGER NOT NULL,
    mastery       REAL    NOT NULL,
    gap_level     TEXT    NOT NULL,
    gap_score     REAL    NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS learning_progress (
    progress_id   SERIAL PRIMARY KEY,
    student_id    INTEGER NOT NULL,
    concept_id    INTEGER NOT NULL,
    learning_step INTEGER NOT NULL,
    status        TEXT    NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS practice_attempts (
    attempt_id     SERIAL PRIMARY KEY,
    student_id     INTEGER NOT NULL,
    question_id    TEXT    NOT NULL,
    student_answer TEXT    NOT NULL,
    is_correct     INTEGER NOT NULL,
    score          REAL    NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reassessments (
    reassessment_id SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL,
    concept_id      INTEGER NOT NULL,
    before_mastery  REAL    NOT NULL,
    after_mastery   REAL    NOT NULL,
    improvement     REAL    NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feynman_attempts (
    attempt_id     SERIAL PRIMARY KEY,
    student_id     INTEGER NOT NULL,
    concept_id     INTEGER NOT NULL,
    explanation    TEXT    NOT NULL,
    score          REAL    NOT NULL,
    feedback       TEXT,
    strengths      TEXT,
    gaps           TEXT,
    suggestions    TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feynman_student
    ON feynman_attempts(student_id);
"""


# ============================================================
# INITIALIZATION
# ============================================================
def initialize_database(db_path=None, verbose=True):
    """
    Create all required tables if they do not exist.

    Uses PostgreSQL if DATABASE_URL is set; SQLite otherwise.
    """
    if IS_POSTGRES:
        import psycopg2

        if verbose:
            print("📂 Using PostgreSQL (DATABASE_URL)")

        connection = psycopg2.connect(DATABASE_URL)
        try:
            cursor = connection.cursor()
            cursor.execute(POSTGRES_SCHEMA)
            connection.commit()

            cursor.execute(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname='public' ORDER BY tablename"
            )
            tables = [row[0] for row in cursor.fetchall()]

            if verbose:
                print("✅ PostgreSQL database initialized.")
                print(f"📋 Tables: {', '.join(tables)}")

            return DATABASE_URL
        finally:
            connection.close()
    else:
        if db_path is None:
            db_path = DB_PATH
        else:
            db_path = Path(db_path)

        db_path.parent.mkdir(parents=True, exist_ok=True)

        if verbose:
            print(f"📂 Database path: {db_path}")

        connection = sqlite3.connect(db_path)
        try:
            connection.executescript(SQLITE_SCHEMA)
            connection.commit()

            cursor = connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]

            if verbose:
                print("✅ SQLite database initialized.")
                print(f"📋 Tables: {', '.join(tables)}")

            return db_path
        finally:
            connection.close()


def database_exists(db_path=None):
    """Return True if the database is initialized."""
    if IS_POSTGRES:
        import psycopg2

        try:
            connection = psycopg2.connect(DATABASE_URL)
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = 'students' LIMIT 1"
                )
                return cursor.fetchone() is not None
            finally:
                connection.close()
        except Exception:
            return False

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
        return cursor.fetchone()[0] > 0
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
