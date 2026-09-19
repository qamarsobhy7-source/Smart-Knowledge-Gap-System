"""
Database layer supporting BOTH SQLite and PostgreSQL.

- If DATABASE_URL is set → uses PostgreSQL (production, persistent).
- Otherwise             → uses SQLite (local dev).

The public API is identical, so the rest of the app
does not need to know which backend is in use.
"""

import os
import sqlite3
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
IS_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))

if IS_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError as exc:
        raise ImportError(
            "psycopg2 is required when DATABASE_URL is set."
        ) from exc


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "smart_knowledge_gap.db"


# ============================================================
# CONNECTION WRAPPER
# ============================================================
class _PostgresCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self):
        return [dict(r) for r in self._cursor.fetchall()]

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return None


class _SQLiteCursor:
    """A cursor wrapper that returns dicts instead of sqlite3.Row."""

    def __init__(self, cursor):
        self._cursor = cursor

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        # sqlite3.Row → dict
        try:
            return dict(row)
        except Exception:
            return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        result = []
        for row in rows:
            if isinstance(row, dict):
                result.append(row)
            else:
                try:
                    result.append(dict(row))
                except Exception:
                    result.append(row)
        return result

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid


class _Connection:
    """A unified connection wrapper for SQLite and PostgreSQL."""

    def __init__(self):
        if IS_POSTGRES:
            self._conn = psycopg2.connect(DATABASE_URL)
        else:
            self._conn = sqlite3.connect(str(DB_PATH))
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.row_factory = sqlite3.Row

    def execute(self, query, params=()):
        if IS_POSTGRES:
            query = query.replace("?", "%s")
            cursor = self._conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            cursor.execute(query, params)
            return _PostgresCursor(cursor)
        cursor = self._conn.execute(query, params)
        return _SQLiteCursor(cursor)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()


def get_connection():
    return _Connection()


# ============================================================
# SQL DIALECT HELPERS
# ============================================================
def _insert_returning_id(connection, query, params):
    """Insert and return the new row's ID (works in both dialects)."""
    if IS_POSTGRES:
        query = query.rstrip().rstrip(";") + " RETURNING student_id"
        cursor = connection.execute(query, params)
        row = cursor.fetchone()
        return int(row["student_id"])
    cursor = connection.execute(query, params)
    return cursor.lastrowid


def _insert_assessment_returning_id(connection, query, params):
    if IS_POSTGRES:
        query = query.rstrip().rstrip(";") + " RETURNING assessment_id"
        cursor = connection.execute(query, params)
        row = cursor.fetchone()
        return int(row["assessment_id"])
    cursor = connection.execute(query, params)
    return cursor.lastrowid


def _insert_answer_returning_id(connection, query, params):
    if IS_POSTGRES:
        query = query.rstrip().rstrip(";") + " RETURNING answer_id"
        cursor = connection.execute(query, params)
        row = cursor.fetchone()
        return int(row["answer_id"])
    cursor = connection.execute(query, params)
    return cursor.lastrowid


def _insert_result_returning_id(connection, query, params):
    if IS_POSTGRES:
        query = query.rstrip().rstrip(";") + " RETURNING result_id"
        cursor = connection.execute(query, params)
        row = cursor.fetchone()
        return int(row["result_id"])
    cursor = connection.execute(query, params)
    return cursor.lastrowid


def _insert_progress_returning_id(connection, query, params):
    if IS_POSTGRES:
        query = query.rstrip().rstrip(";") + " RETURNING progress_id"
        cursor = connection.execute(query, params)
        row = cursor.fetchone()
        return int(row["progress_id"])
    cursor = connection.execute(query, params)
    return cursor.lastrowid


def _insert_practice_returning_id(connection, query, params):
    if IS_POSTGRES:
        query = query.rstrip().rstrip(";") + " RETURNING attempt_id"
        cursor = connection.execute(query, params)
        row = cursor.fetchone()
        return int(row["attempt_id"])
    cursor = connection.execute(query, params)
    return cursor.lastrowid


def _insert_reassess_returning_id(connection, query, params):
    if IS_POSTGRES:
        query = query.rstrip().rstrip(";") + " RETURNING reassessment_id"
        cursor = connection.execute(query, params)
        row = cursor.fetchone()
        return int(row["reassessment_id"])
    cursor = connection.execute(query, params)
    return cursor.lastrowid




# ============================================================
# STUDENT CRUD
# ============================================================
def create_student(full_name, email=None, password_hash=None):
    if not full_name or not str(full_name).strip():
        raise ValueError("Student name is required.")

    if email is not None:
        email = str(email).strip().lower()
        if not email:
            email = None

    try:
        with get_connection() as connection:
            query = """
                INSERT INTO students (full_name, email, password_hash)
                VALUES (?, ?, ?)
            """
            params = (
                str(full_name).strip(),
                email,
                password_hash,
            )
            return _insert_returning_id(connection, query, params)
    except Exception as exc:
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise ValueError("Email is already registered.")
        raise


def get_student(student_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                student_id,
                full_name,
                email,
                created_at
            FROM students
            WHERE student_id = ?
            """,
            (int(student_id),)
        )
        return cursor.fetchone()


def get_student_by_email(email):
    if not email:
        return None

    email = str(email).strip().lower()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                student_id,
                full_name,
                email,
                password_hash,
                created_at
            FROM students
            WHERE email = ?
            """,
            (email,)
        )
        return cursor.fetchone()


# ============================================================
# PASSWORD RESET
# ============================================================
def set_password_reset_token(email, token, expires_at):
    if not email:
        return False

    email = str(email).strip().lower()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE students
            SET password_reset_token = ?,
                password_reset_expires = ?
            WHERE email = ?
            """,
            (str(token), expires_at, email)
        )
        return cursor.rowcount > 0


def get_student_by_reset_token(token):
    if not token:
        return None

    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                student_id,
                full_name,
                email,
                password_hash,
                password_reset_token,
                password_reset_expires
            FROM students
            WHERE password_reset_token = ?
            """,
            (str(token),)
        )
        return cursor.fetchone()


def update_password(student_id, password_hash):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE students
            SET password_hash = ?,
                password_reset_token = NULL,
                password_reset_expires = NULL
            WHERE student_id = ?
            """,
            (password_hash, int(student_id))
        )
        return cursor.rowcount > 0


# ============================================================
# ASSESSMENT CRUD
# ============================================================
def create_assessment(student_id, assessment_type):
    if not assessment_type or not str(assessment_type).strip():
        raise ValueError("Assessment type is required.")

    with get_connection() as connection:
        query = """
            INSERT INTO assessments (student_id, assessment_type)
            VALUES (?, ?)
        """
        params = (
            int(student_id),
            str(assessment_type).strip()
        )
        return _insert_assessment_returning_id(connection, query, params)


def save_answer(
    assessment_id,
    question_id,
    student_answer,
    is_correct,
    score
):
    with get_connection() as connection:
        query = """
            INSERT INTO answers (
                assessment_id,
                question_id,
                student_answer,
                is_correct,
                score
            )
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            int(assessment_id),
            str(question_id),
            student_answer,
            int(bool(is_correct)),
            float(score)
        )
        return _insert_answer_returning_id(connection, query, params)


def save_concept_result(
    assessment_id,
    concept_id,
    mastery,
    gap_level,
    gap_score
):
    mastery = float(mastery)
    gap_score = float(gap_score)

    if not 0.0 <= mastery <= 100.0:
        raise ValueError("Mastery must be between 0 and 100.")

    if not 0.0 <= gap_score <= 100.0:
        raise ValueError("Gap score must be between 0 and 100.")

    with get_connection() as connection:
        query = """
            INSERT INTO concept_results (
                assessment_id,
                concept_id,
                mastery,
                gap_level,
                gap_score
            )
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            int(assessment_id),
            int(concept_id),
            mastery,
            str(gap_level),
            gap_score
        )
        return _insert_result_returning_id(connection, query, params)


def save_learning_progress(
    student_id,
    concept_id,
    learning_step,
    status
):
    if not status or not str(status).strip():
        raise ValueError("Learning status is required.")

    with get_connection() as connection:
        query = """
            INSERT INTO learning_progress (
                student_id,
                concept_id,
                learning_step,
                status
            )
            VALUES (?, ?, ?, ?)
        """
        params = (
            int(student_id),
            int(concept_id),
            int(learning_step),
            str(status).strip()
        )
        return _insert_progress_returning_id(connection, query, params)


def save_practice_attempt(
    student_id,
    question_id,
    student_answer,
    is_correct,
    score
):
    with get_connection() as connection:
        query = """
            INSERT INTO practice_attempts (
                student_id,
                question_id,
                student_answer,
                is_correct,
                score
            )
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            int(student_id),
            str(question_id),
            student_answer,
            int(bool(is_correct)),
            float(score)
        )
        return _insert_practice_returning_id(connection, query, params)


def save_reassessment(
    student_id,
    concept_id,
    before_mastery,
    after_mastery,
    improvement
):
    before_mastery = float(before_mastery)
    after_mastery = float(after_mastery)
    improvement = float(improvement)

    if not 0.0 <= before_mastery <= 100.0:
        raise ValueError(
            "Before mastery must be between 0 and 100."
        )

    if not 0.0 <= after_mastery <= 100.0:
        raise ValueError(
            "After mastery must be between 0 and 100."
        )

    expected_improvement = after_mastery - before_mastery

    if abs(improvement - expected_improvement) > 1e-9:
        raise ValueError(
            "Improvement does not match before/after mastery."
        )

    with get_connection() as connection:
        query = """
            INSERT INTO reassessments (
                student_id,
                concept_id,
                before_mastery,
                after_mastery,
                improvement
            )
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            int(student_id),
            int(concept_id),
            before_mastery,
            after_mastery,
            improvement
        )
        return _insert_reassess_returning_id(connection, query, params)


# ============================================================
# QUERIES
# ============================================================
def get_assessment_answers(assessment_id):
    if assessment_id is None:
        raise ValueError("Assessment ID is required.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                answer_id,
                assessment_id,
                question_id,
                student_answer,
                is_correct,
                score
            FROM answers
            WHERE assessment_id = ?
            ORDER BY answer_id ASC
            """,
            (int(assessment_id),)
        )
        return cursor.fetchall()


def get_latest_diagnostic_assessment(student_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                assessment_id,
                student_id,
                assessment_type,
                created_at
            FROM assessments
            WHERE
                student_id = ?
                AND assessment_type = 'Diagnostic'
            ORDER BY
                created_at DESC,
                assessment_id DESC
            """,
            (int(student_id),)
        )
        rows = cursor.fetchall()
        return rows[0] if rows else None


def get_concept_results_for_assessment(assessment_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                result_id,
                assessment_id,
                concept_id,
                mastery,
                gap_level,
                gap_score
            FROM concept_results
            WHERE assessment_id = ?
            ORDER BY concept_id ASC
            """,
            (int(assessment_id),)
        )
        return cursor.fetchall()


# ============================================================
# FEYNMAN BOARD
# ============================================================
def save_feynman_attempt(
    student_id,
    concept_id,
    explanation,
    score,
    feedback=None,
    strengths=None,
    gaps=None,
    suggestions=None,
):
    """Save a Feynman explanation attempt."""
    if not explanation or not str(explanation).strip():
        raise ValueError("Explanation is required.")

    score = float(score)
    if not 0.0 <= score <= 100.0:
        raise ValueError("Score must be between 0 and 100.")

    with get_connection() as connection:
        query = """
            INSERT INTO feynman_attempts (
                student_id,
                concept_id,
                explanation,
                score,
                feedback,
                strengths,
                gaps,
                suggestions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            int(student_id),
            int(concept_id),
            str(explanation).strip(),
            score,
            feedback,
            strengths,
            gaps,
            suggestions,
        )
        return _insert_returning_id(connection, query, params)


def get_feynman_attempts(student_id, concept_id=None, limit=10):
    """Get Feynman attempts for a student, optionally filtered by concept."""
    with get_connection() as connection:
        if concept_id is not None:
            cursor = connection.execute(
                """
                SELECT
                    attempt_id,
                    student_id,
                    concept_id,
                    explanation,
                    score,
                    feedback,
                    strengths,
                    gaps,
                    suggestions,
                    created_at
                FROM feynman_attempts
                WHERE student_id = ? AND concept_id = ?
                ORDER BY attempt_id DESC
                """,
                (int(student_id), int(concept_id)),
            )
        else:
            cursor = connection.execute(
                """
                SELECT
                    attempt_id,
                    student_id,
                    concept_id,
                    explanation,
                    score,
                    feedback,
                    strengths,
                    gaps,
                    suggestions,
                    created_at
                FROM feynman_attempts
                WHERE student_id = ?
                ORDER BY attempt_id DESC
                """,
                (int(student_id),),
            )
        rows = cursor.fetchall()
        return rows[:limit]


def get_latest_feynman_attempt(student_id, concept_id):
    """Get the latest Feynman attempt for a student + concept."""
    attempts = get_feynman_attempts(
        student_id=student_id,
        concept_id=concept_id,
        limit=1,
    )
    return attempts[0] if attempts else None


def assessment_exists(assessment_id):
    """Return True if the assessment row exists."""
    if assessment_id is None:
        return False
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT 1 FROM assessments WHERE assessment_id = ? LIMIT 1",
            (int(assessment_id),),
        )
        return cursor.fetchone() is not None
