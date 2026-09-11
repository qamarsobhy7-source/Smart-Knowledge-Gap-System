
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "smart_knowledge_gap.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def create_student(full_name):
    if not full_name or not str(full_name).strip():
        raise ValueError("Student name is required.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO students (full_name)
            VALUES (?)
            """,
            (str(full_name).strip(),)
        )

        return cursor.lastrowid


def get_student(student_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                student_id,
                full_name,
                created_at
            FROM students
            WHERE student_id = ?
            """,
            (int(student_id),)
        ).fetchone()

        return dict(row) if row else None


def create_assessment(student_id, assessment_type):
    if not assessment_type or not str(assessment_type).strip():
        raise ValueError("Assessment type is required.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO assessments (
                student_id,
                assessment_type
            )
            VALUES (?, ?)
            """,
            (
                int(student_id),
                str(assessment_type).strip()
            )
        )

        return cursor.lastrowid


def save_answer(
    assessment_id,
    question_id,
    student_answer,
    is_correct,
    score
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO answers (
                assessment_id,
                question_id,
                student_answer,
                is_correct,
                score
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(assessment_id),
                str(question_id),
                student_answer,
                int(bool(is_correct)),
                float(score)
            )
        )

        return cursor.lastrowid


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
        cursor = connection.execute(
            """
            INSERT INTO concept_results (
                assessment_id,
                concept_id,
                mastery,
                gap_level,
                gap_score
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(assessment_id),
                int(concept_id),
                mastery,
                str(gap_level),
                gap_score
            )
        )

        return cursor.lastrowid


def save_learning_progress(
    student_id,
    concept_id,
    learning_step,
    status
):
    if not status or not str(status).strip():
        raise ValueError("Learning status is required.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO learning_progress (
                student_id,
                concept_id,
                learning_step,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                int(student_id),
                int(concept_id),
                int(learning_step),
                str(status).strip()
            )
        )

        return cursor.lastrowid


def save_practice_attempt(
    student_id,
    question_id,
    student_answer,
    is_correct,
    score
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO practice_attempts (
                student_id,
                question_id,
                student_answer,
                is_correct,
                score
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(student_id),
                str(question_id),
                student_answer,
                int(bool(is_correct)),
                float(score)
            )
        )

        return cursor.lastrowid


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
        cursor = connection.execute(
            """
            INSERT INTO reassessments (
                student_id,
                concept_id,
                before_mastery,
                after_mastery,
                improvement
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(student_id),
                int(concept_id),
                before_mastery,
                after_mastery,
                improvement
            )
        )

        return cursor.lastrowid

def get_assessment_answers(assessment_id):
    if assessment_id is None:
        raise ValueError(
            "Assessment ID is required."
        )

    with get_connection() as connection:
        rows = connection.execute(
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
        ).fetchall()

        return [dict(row) for row in rows]

