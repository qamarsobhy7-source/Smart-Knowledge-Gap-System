
from pathlib import Path
import sqlite3

import pandas as pd

try:
    from .database import get_connection
except ImportError:
    from database import get_connection
try:
    from .repository import load_concepts
except ImportError:
    from repository import load_concepts
try:
    from .priority_engine import calculate_student_priority
except ImportError:
    from priority_engine import calculate_student_priority


def _empty_teacher_dashboard():
    return {
        "overview": {
            "total_students": 0,
            "total_assessments": 0,
            "completed_diagnostic_assessments": 0,
            "total_concept_results": 0,
            "total_practice_attempts": 0,
            "total_learning_progress_records": 0,
            "total_reassessments": 0
        },
        "students": [],
        "concept_performance": [],
        "knowledge_gaps": [],
        "student_performance": [],
        "learning_priorities": [],
        "learning_progress": [],
        "practice_activity": [],
        "reassessment_and_improvement": [],
        "activity_summary": {
            "practice_attempts": 0,
            "learning_progress_records": 0,
            "reassessments": 0,
            "average_before_mastery": None,
            "average_after_mastery": None,
            "average_improvement": None
        }
    }


def _get_student_records(connection, concepts_df):
    rows = connection.execute(
        """
        SELECT
            s.student_id,
            s.full_name,
            s.created_at,
            COUNT(DISTINCT a.assessment_id) AS assessment_count,
            COUNT(DISTINCT cr.result_id) AS concept_results,
            COUNT(DISTINCT pa.attempt_id) AS practice_attempts,
            COUNT(DISTINCT lp.progress_id) AS learning_progress_records,
            COUNT(DISTINCT r.reassessment_id) AS reassessments
        FROM students s
        LEFT JOIN assessments a
            ON a.student_id = s.student_id
        LEFT JOIN concept_results cr
            ON cr.assessment_id = a.assessment_id
        LEFT JOIN practice_attempts pa
            ON pa.student_id = s.student_id
        LEFT JOIN learning_progress lp
            ON lp.student_id = s.student_id
        LEFT JOIN reassessments r
            ON r.student_id = s.student_id
        GROUP BY
            s.student_id,
            s.full_name,
            s.created_at
        ORDER BY
            s.student_id ASC
        """
    ).fetchall()

    records = []

    for row in rows:
        student_id = int(row["student_id"])

        latest = connection.execute(
            """
            SELECT
                assessment_id,
                assessment_type,
                created_at
            FROM assessments
            WHERE student_id = ?
              AND EXISTS (
                  SELECT 1
                  FROM concept_results
                  WHERE concept_results.assessment_id =
                        assessments.assessment_id
              )
            ORDER BY assessment_id DESC
            LIMIT 1
            """,
            (student_id,)
        ).fetchone()

        overall_mastery = None
        strong_concepts = 0
        weak_concepts = 0
        critical_concepts = 0

        if latest is not None:
            mastery_row = connection.execute(
                """
                SELECT
                    AVG(mastery) AS overall_mastery
                FROM concept_results
                WHERE assessment_id = ?
                """,
                (int(latest["assessment_id"]),)
            ).fetchone()

            if (
                mastery_row is not None
                and mastery_row["overall_mastery"] is not None
            ):
                overall_mastery = float(
                    mastery_row["overall_mastery"]
                )

            gap_rows = connection.execute(
                """
                SELECT
                    gap_level,
                    COUNT(*) AS count
                FROM concept_results
                WHERE assessment_id = ?
                GROUP BY gap_level
                """,
                (int(latest["assessment_id"]),)
            ).fetchall()

            for gap_row in gap_rows:
                level = str(
                    gap_row["gap_level"]
                ).strip().lower()

                count = int(gap_row["count"])

                if level == "strong":
                    strong_concepts = count
                elif level == "weak":
                    weak_concepts = count
                elif level == "critical":
                    critical_concepts = count

        records.append(
            {
                "student_id": student_id,
                "full_name": row["full_name"],
                "created_at": row["created_at"],
                "assessment_count": int(
                    row["assessment_count"]
                ),
                "latest_assessment_type": (
                    latest["assessment_type"]
                    if latest is not None
                    else None
                ),
                "latest_assessment_date": (
                    latest["created_at"]
                    if latest is not None
                    else None
                ),
                "overall_mastery": overall_mastery,
                "concepts_assessed": int(
                    row["concept_results"]
                ),
                "strong_concepts": strong_concepts,
                "weak_concepts": weak_concepts,
                "critical_concepts": critical_concepts,
                "practice_attempts": int(
                    row["practice_attempts"]
                ),
                "learning_progress_records": int(
                    row["learning_progress_records"]
                ),
                "reassessments": int(
                    row["reassessments"]
                )
            }
        )

    return records


def _get_concept_performance(connection, concepts_df):
    rows = connection.execute(
        """
        SELECT
            concept_id,
            COUNT(*) AS students_assessed,
            AVG(mastery) AS average_mastery,
            MIN(mastery) AS minimum_mastery,
            MAX(mastery) AS maximum_mastery
        FROM concept_results
        GROUP BY concept_id
        ORDER BY concept_id ASC
        """
    ).fetchall()

    if not rows:
        return []

    concept_lookup = (
        concepts_df[
            [
                "concept_id",
                "concept_name",
                "subject_id",
                "difficulty"
            ]
        ]
        .copy()
    )

    concept_lookup["concept_id"] = (
        concept_lookup["concept_id"].astype(int)
    )

    records = []

    for row in rows:
        concept_id = int(row["concept_id"])

        matches = concept_lookup[
            concept_lookup["concept_id"] == concept_id
        ]

        if matches.empty:
            raise ValueError(
                f"Unknown concept_id in concept_results: "
                f"{concept_id}"
            )

        concept = matches.iloc[0]

        records.append(
            {
                "concept_id": concept_id,
                "concept_name": concept["concept_name"],
                "subject_id": concept["subject_id"],
                "difficulty": concept["difficulty"],
                "students_assessed": int(
                    row["students_assessed"]
                ),
                "average_mastery": float(
                    row["average_mastery"]
                ),
                "minimum_mastery": float(
                    row["minimum_mastery"]
                ),
                "maximum_mastery": float(
                    row["maximum_mastery"]
                )
            }
        )

    return records


def _get_knowledge_gaps(connection, concepts_df):
    rows = connection.execute(
        """
        SELECT
            concept_id,
            COUNT(*) AS students_with_gap,
            AVG(mastery) AS average_mastery
        FROM concept_results
        WHERE gap_level IN ('Weak', 'Critical')
        GROUP BY concept_id
        ORDER BY
            students_with_gap DESC,
            average_mastery ASC,
            concept_id ASC
        """
    ).fetchall()

    if not rows:
        return []

    concept_lookup = (
        concepts_df[
            [
                "concept_id",
                "concept_name"
            ]
        ]
        .copy()
    )

    concept_lookup["concept_id"] = (
        concept_lookup["concept_id"].astype(int)
    )

    records = []

    for row in rows:
        concept_id = int(row["concept_id"])

        matches = concept_lookup[
            concept_lookup["concept_id"] == concept_id
        ]

        if matches.empty:
            raise ValueError(
                f"Unknown concept_id in gap results: "
                f"{concept_id}"
            )

        concept = matches.iloc[0]

        records.append(
            {
                "concept_id": concept_id,
                "concept_name": concept["concept_name"],
                "students_with_gap": int(
                    row["students_with_gap"]
                ),
                "average_mastery": float(
                    row["average_mastery"]
                )
            }
        )

    return records


def _get_activity_summary(connection):
    practice_attempts = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM practice_attempts
        """
    ).fetchone()["count"]

    learning_progress_records = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM learning_progress
        """
    ).fetchone()["count"]

    reassessments = connection.execute(
        """
        SELECT
            COUNT(*) AS count,
            AVG(before_mastery) AS average_before_mastery,
            AVG(after_mastery) AS average_after_mastery,
            AVG(improvement) AS average_improvement
        FROM reassessments
        """
    ).fetchone()

    return {
        "practice_attempts": int(
            practice_attempts
        ),
        "learning_progress_records": int(
            learning_progress_records
        ),
        "reassessments": int(
            reassessments["count"]
        ),
        "average_before_mastery": (
            float(reassessments["average_before_mastery"])
            if reassessments["average_before_mastery"]
            is not None
            else None
        ),
        "average_after_mastery": (
            float(reassessments["average_after_mastery"])
            if reassessments["average_after_mastery"]
            is not None
            else None
        ),
        "average_improvement": (
            float(reassessments["average_improvement"])
            if reassessments["average_improvement"]
            is not None
            else None
        )
    }




def _get_student_performance(connection):
    """
    Return latest diagnostic performance for each student.
    """

    students = connection.execute(
        """
        SELECT
            student_id,
            full_name
        FROM students
        ORDER BY student_id ASC
        """
    ).fetchall()

    records = []

    for student in students:
        student_id = int(
            student["student_id"]
        )

        latest = connection.execute(
            """
            SELECT
                assessment_id,
                assessment_type,
                created_at
            FROM assessments
            WHERE student_id = ?
              AND EXISTS (
                  SELECT 1
                  FROM concept_results
                  WHERE concept_results.assessment_id =
                        assessments.assessment_id
              )
            ORDER BY assessment_id DESC
            LIMIT 1
            """,
            (student_id,)
        ).fetchone()

        if latest is None:
            records.append({
                "student_id": student_id,
                "full_name": student["full_name"],
                "assessment_id": None,
                "assessment_type": None,
                "assessment_created_at": None,
                "overall_mastery": None,
                "strong_concepts": 0,
                "weak_concepts": 0,
                "critical_concepts": 0
            })
            continue

        rows = connection.execute(
            """
            SELECT
                mastery,
                gap_level
            FROM concept_results
            WHERE assessment_id = ?
            """,
            (int(latest["assessment_id"]),)
        ).fetchall()

        if rows:
            mastery_values = [
                float(row["mastery"])
                for row in rows
            ]

            overall_mastery = (
                sum(mastery_values)
                / len(mastery_values)
            )

            strong_concepts = sum(
                str(row["gap_level"]).strip().lower()
                == "strong"
                for row in rows
            )

            weak_concepts = sum(
                str(row["gap_level"]).strip().lower()
                == "weak"
                for row in rows
            )

            critical_concepts = sum(
                str(row["gap_level"]).strip().lower()
                == "critical"
                for row in rows
            )

        else:
            overall_mastery = None
            strong_concepts = 0
            weak_concepts = 0
            critical_concepts = 0

        records.append({
            "student_id": student_id,
            "full_name": student["full_name"],
            "assessment_id": int(
                latest["assessment_id"]
            ),
            "assessment_type": (
                latest["assessment_type"]
            ),
            "assessment_created_at": (
                latest["created_at"]
            ),
            "overall_mastery": (
                float(overall_mastery)
                if overall_mastery is not None
                else None
            ),
            "strong_concepts": int(
                strong_concepts
            ),
            "weak_concepts": int(
                weak_concepts
            ),
            "critical_concepts": int(
                critical_concepts
            )
        })

    return records


def _get_learning_priorities(
    connection,
    concepts_df
):
    """
    Reuse the existing Priority Engine for
    student-specific learning priorities.
    """

    students = connection.execute(
        """
        SELECT student_id
        FROM students
        ORDER BY student_id ASC
        """
    ).fetchall()

    records = []

    for student in students:
        student_id = int(
            student["student_id"]
        )

        latest = connection.execute(
            """
            SELECT assessment_id
            FROM assessments
            WHERE student_id = ?
              AND EXISTS (
                  SELECT 1
                  FROM concept_results
                  WHERE concept_results.assessment_id =
                        assessments.assessment_id
              )
            ORDER BY assessment_id DESC
            LIMIT 1
            """,
            (student_id,)
        ).fetchone()

        if latest is None:
            continue

        rows = connection.execute(
            """
            SELECT
                concept_id,
                mastery,
                gap_level,
                gap_score
            FROM concept_results
            WHERE assessment_id = ?
            ORDER BY concept_id ASC
            """,
            (int(latest["assessment_id"]),)
        ).fetchall()

        if not rows:
            continue

        diagnosis_df = pd.DataFrame(
            [dict(row) for row in rows]
        )

        diagnosis_df["concept_id"] = (
            diagnosis_df["concept_id"].astype(int)
        )

        priority_df = calculate_student_priority(
            diagnosis_df,
            concepts_df
        )

        if priority_df is None:
            continue

        if priority_df.empty:
            continue

        concept_lookup = concepts_df[
            [
                "concept_id",
                "concept_name",
                "subject_id",
                "difficulty"
            ]
        ].copy()

        concept_lookup["concept_id"] = (
            concept_lookup["concept_id"].astype(int)
        )

        priority_df = priority_df.merge(
            concept_lookup,
            on="concept_id",
            how="left",
            validate="one_to_one"
        )

        if priority_df["concept_name"].isna().any():
            raise RuntimeError(
                "Learning priority concept mapping failed."
            )

        for _, row in priority_df.iterrows():
            records.append({
                "student_id": student_id,
                "concept_id": int(
                    row["concept_id"]
                ),
                "concept_name": row["concept_name"],
                "subject_id": row["subject_id"],
                "difficulty": row["difficulty"],
                "mastery": float(
                    row["mastery"]
                ),
                "gap_level": row["gap_level"],
                "gap_score": float(
                    row["gap_score"]
                ),
                "priority_score": float(
                    row["priority_score"]
                ),
                "priority_level": row["priority_level"],
                "priority_rank": int(
                    row["priority_rank"]
                )
            })

    records.sort(
        key=lambda item: (
            item["student_id"],
            item["priority_rank"]
        )
    )

    return records


def _get_learning_progress(
    connection,
    concepts_df
):
    """
    Return the latest learning-progress record
    for each student and concept.
    """

    rows = connection.execute(
        """
        SELECT
            progress_id,
            student_id,
            concept_id,
            learning_step,
            status,
            created_at
        FROM learning_progress
        ORDER BY
            student_id ASC,
            progress_id ASC
        """
    ).fetchall()

    if not rows:
        return []

    progress_df = pd.DataFrame(
        [dict(row) for row in rows]
    )

    progress_df["concept_id"] = (
        progress_df["concept_id"].astype(int)
    )

    concept_lookup = concepts_df[
        [
            "concept_id",
            "concept_name",
            "subject_id"
        ]
    ].copy()

    concept_lookup["concept_id"] = (
        concept_lookup["concept_id"].astype(int)
    )

    progress_df = progress_df.merge(
        concept_lookup,
        on="concept_id",
        how="left",
        validate="many_to_one"
    )

    if progress_df["concept_name"].isna().any():
        raise RuntimeError(
            "Learning progress concept mapping failed."
        )

    progress_df = (
        progress_df
        .sort_values("progress_id")
        .drop_duplicates(
            subset=[
                "student_id",
                "concept_id"
            ],
            keep="last"
        )
        .sort_values(
            [
                "student_id",
                "learning_step",
                "concept_id"
            ]
        )
    )

    return (
        progress_df[
            [
                "student_id",
                "progress_id",
                "concept_id",
                "concept_name",
                "subject_id",
                "learning_step",
                "status",
                "created_at"
            ]
        ]
        .to_dict(orient="records")
    )


def _get_practice_activity(connection):
    """
    Return teacher-level practice activity
    per student.
    """

    rows = connection.execute(
        """
        SELECT
            student_id,
            COUNT(*) AS total_attempts,
            SUM(
                CASE
                    WHEN is_correct = 1
                    THEN 1
                    ELSE 0
                END
            ) AS correct_attempts,
            AVG(score) AS average_score,
            MAX(created_at) AS last_attempt_at
        FROM practice_attempts
        GROUP BY student_id
        ORDER BY student_id ASC
        """
    ).fetchall()

    records = []

    for row in rows:
        total_attempts = int(
            row["total_attempts"]
        )

        correct_attempts = int(
            row["correct_attempts"] or 0
        )

        accuracy = (
            (
                float(correct_attempts)
                / float(total_attempts)
                * 100.0
            )
            if total_attempts > 0
            else None
        )

        records.append({
            "student_id": int(
                row["student_id"]
            ),
            "practice_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "accuracy": accuracy,
            "average_score": (
                float(row["average_score"])
                if row["average_score"] is not None
                else None
            ),
            "last_attempt_at": (
                str(row["last_attempt_at"])
                if row["last_attempt_at"] is not None
                else None
            )
        })

    return records


def _get_reassessment_and_improvement(
    connection
):
    """
    Return reassessment and improvement
    statistics per student.
    """

    rows = connection.execute(
        """
        SELECT
            student_id,
            COUNT(*) AS total_reassessments,
            COUNT(DISTINCT concept_id)
                AS concepts_reassessed,
            AVG(before_mastery)
                AS average_before_mastery,
            AVG(after_mastery)
                AS average_after_mastery,
            AVG(improvement)
                AS average_improvement
        FROM reassessments
        GROUP BY student_id
        ORDER BY student_id ASC
        """
    ).fetchall()

    records = []

    for row in rows:
        records.append({
            "student_id": int(
                row["student_id"]
            ),
            "total_reassessments": int(
                row["total_reassessments"]
            ),
            "concepts_reassessed": int(
                row["concepts_reassessed"]
            ),
            "average_before_mastery": (
                float(
                    row["average_before_mastery"]
                )
                if row["average_before_mastery"]
                is not None
                else None
            ),
            "average_after_mastery": (
                float(
                    row["average_after_mastery"]
                )
                if row["average_after_mastery"]
                is not None
                else None
            ),
            "average_improvement": (
                float(
                    row["average_improvement"]
                )
                if row["average_improvement"]
                is not None
                else None
            )
        })

    return records


def get_teacher_dashboard_data():
    concepts_df = load_concepts()

    if concepts_df.empty:
        raise ValueError(
            "Concept master is empty."
        )

    with get_connection() as connection:
        students_count = connection.execute(
            "SELECT COUNT(*) AS count FROM students"
        ).fetchone()["count"]

        assessments_count = connection.execute(
            "SELECT COUNT(*) AS count FROM assessments"
        ).fetchone()["count"]

        diagnostic_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM assessments
            WHERE assessment_type = 'Diagnostic'
            """
        ).fetchone()["count"]

        concept_results_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM concept_results
            """
        ).fetchone()["count"]

        practice_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM practice_attempts
            """
        ).fetchone()["count"]

        progress_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM learning_progress
            """
        ).fetchone()["count"]

        reassessment_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM reassessments
            """
        ).fetchone()["count"]

        if int(students_count) == 0:
            return _empty_teacher_dashboard()

        student_records = _get_student_records(
            connection,
            concepts_df
        )

        student_performance = (
            _get_student_performance(
                connection
            )
        )

        learning_priorities = (
            _get_learning_priorities(
                connection,
                concepts_df
            )
        )

        learning_progress = (
            _get_learning_progress(
                connection,
                concepts_df
            )
        )

        practice_activity = (
            _get_practice_activity(
                connection
            )
        )

        reassessment_and_improvement = (
            _get_reassessment_and_improvement(
                connection
            )
        )

        return {
            "overview": {
                "total_students": int(students_count),
                "total_assessments": int(
                    assessments_count
                ),
                "completed_diagnostic_assessments": int(
                    diagnostic_count
                ),
                "total_concept_results": int(
                    concept_results_count
                ),
                "total_practice_attempts": int(
                    practice_count
                ),
                "total_learning_progress_records": int(
                    progress_count
                ),
                "total_reassessments": int(
                    reassessment_count
                )
            },
            "students": student_records,
            "student_performance": (
                student_performance
            ),
            "concept_performance": (
                _get_concept_performance(
                    connection,
                    concepts_df
                )
            ),
            "knowledge_gaps": _get_knowledge_gaps(
                connection,
                concepts_df
            ),
            "learning_priorities": (
                learning_priorities
            ),
            "learning_progress": (
                learning_progress
            ),
            "practice_activity": (
                practice_activity
            ),
            "reassessment_and_improvement": (
                reassessment_and_improvement
            ),
            "activity_summary": (
                _get_activity_summary(
                    connection
                )
            )
        }
