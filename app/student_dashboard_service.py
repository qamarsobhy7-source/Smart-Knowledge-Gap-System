import pandas as pd

from database import get_connection

from repository import (
    load_concepts,
    load_question_bank
)

from priority_engine import (
    calculate_student_priority
)

from learning_path_engine import (
    build_personalized_learning_path
)



def _get_student_activity_data(
    connection,
    student_id,
    concepts_df
):
    """
    Collect student-specific learning activity.

    Empty activity is valid for a newly registered student.
    """

    student_id = int(student_id)

    # --------------------------------------------------------------
    # Practice attempts
    # --------------------------------------------------------------
    practice_rows = connection.execute(
        """
        SELECT
            attempt_id,
            student_id,
            question_id,
            student_answer,
            is_correct,
            score,
            created_at
        FROM practice_attempts
        WHERE student_id = ?
        ORDER BY attempt_id ASC
        """,
        (student_id,)
    ).fetchall()

    practice_df = pd.DataFrame(
        [dict(row) for row in practice_rows]
    )

    practice_summary = {
        "total_attempts": 0,
        "correct_attempts": 0,
        "accuracy": None,
        "average_score": None,
        "last_attempt_at": None
    }

    practice_records = []

    if not practice_df.empty:

        question_bank_df = load_question_bank()

        required_fields = {
            "question_id",
            "concept_id"
        }

        if not required_fields.issubset(
            question_bank_df.columns
        ):
            raise RuntimeError(
                "Question Bank is missing "
                "question_id/concept_id fields."
            )

        question_map = question_bank_df[
            [
                "question_id",
                "concept_id"
            ]
        ].copy()

        question_map["question_id"] = (
            question_map["question_id"].astype(str)
        )

        question_map["concept_id"] = (
            question_map["concept_id"].astype(int)
        )

        practice_df["question_id"] = (
            practice_df["question_id"].astype(str)
        )

        practice_df = practice_df.merge(
            question_map,
            on="question_id",
            how="left",
            validate="many_to_one"
        )

        if practice_df["concept_id"].isna().any():
            raise RuntimeError(
                "Practice attempt question-to-concept "
                "mapping failed."
            )

        practice_df["concept_id"] = (
            practice_df["concept_id"].astype(int)
        )

        concept_names = concepts_df[
            [
                "concept_id",
                "concept_name"
            ]
        ].copy()

        concept_names["concept_id"] = (
            concept_names["concept_id"].astype(int)
        )

        practice_df = practice_df.merge(
            concept_names,
            on="concept_id",
            how="left",
            validate="many_to_one"
        )

        if practice_df["concept_name"].isna().any():
            raise RuntimeError(
                "Practice attempt concept-name mapping failed."
            )

        practice_summary = {
            "total_attempts": int(len(practice_df)),
            "correct_attempts": int(
                practice_df["is_correct"]
                .astype(int)
                .sum()
            ),
            "accuracy": float(
                practice_df["is_correct"]
                .astype(int)
                .mean()
                * 100.0
            ),
            "average_score": float(
                practice_df["score"]
                .astype(float)
                .mean()
            ),
            "last_attempt_at": str(
                practice_df.iloc[-1]["created_at"]
            )
        }

        practice_records = (
            practice_df[
                [
                    "attempt_id",
                    "question_id",
                    "concept_id",
                    "concept_name",
                    "student_answer",
                    "is_correct",
                    "score",
                    "created_at"
                ]
            ]
            .to_dict(orient="records")
        )

    # --------------------------------------------------------------
    # Learning progress
    # --------------------------------------------------------------
    progress_rows = connection.execute(
        """
        SELECT
            progress_id,
            student_id,
            concept_id,
            learning_step,
            status,
            created_at
        FROM learning_progress
        WHERE student_id = ?
        ORDER BY progress_id ASC
        """,
        (student_id,)
    ).fetchall()

    progress_df = pd.DataFrame(
        [dict(row) for row in progress_rows]
    )

    learning_progress_records = []

    if not progress_df.empty:

        progress_df["concept_id"] = (
            progress_df["concept_id"].astype(int)
        )

        progress_df = progress_df.merge(
            concepts_df[
                [
                    "concept_id",
                    "concept_name",
                    "subject_id"
                ]
            ],
            on="concept_id",
            how="left",
            validate="many_to_one"
        )

        if progress_df["concept_name"].isna().any():
            raise RuntimeError(
                "Learning progress concept mapping failed."
            )

        if progress_df["subject_id"].isna().any():
            raise RuntimeError(
                "Learning progress subject mapping failed."
            )

        progress_df = (
            progress_df
            .sort_values("progress_id")
            .drop_duplicates(
                subset=["concept_id"],
                keep="last"
            )
        )

        learning_progress_records = (
            progress_df[
                [
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

    # --------------------------------------------------------------
    # Re-assessments
    # --------------------------------------------------------------
    reassessment_rows = connection.execute(
        """
        SELECT
            reassessment_id,
            student_id,
            concept_id,
            before_mastery,
            after_mastery,
            improvement,
            created_at
        FROM reassessments
        WHERE student_id = ?
        ORDER BY reassessment_id ASC
        """,
        (student_id,)
    ).fetchall()

    reassessment_df = pd.DataFrame(
        [dict(row) for row in reassessment_rows]
    )

    reassessment_records = []

    reassessment_summary = {
        "total_reassessments": 0,
        "concepts_reassessed": 0,
        "average_before_mastery": None,
        "average_after_mastery": None,
        "average_improvement": None
    }

    if not reassessment_df.empty:

        reassessment_df["concept_id"] = (
            reassessment_df["concept_id"].astype(int)
        )

        reassessment_df = reassessment_df.merge(
            concepts_df[
                [
                    "concept_id",
                    "concept_name",
                    "subject_id"
                ]
            ],
            on="concept_id",
            how="left",
            validate="many_to_one"
        )

        if reassessment_df["concept_name"].isna().any():
            raise RuntimeError(
                "Re-assessment concept mapping failed."
            )

        if reassessment_df["subject_id"].isna().any():
            raise RuntimeError(
                "Re-assessment subject mapping failed."
            )

        total_reassessments = len(reassessment_df)

        reassessment_df = (
            reassessment_df
            .sort_values("reassessment_id")
            .drop_duplicates(
                subset=["concept_id"],
                keep="last"
            )
        )

        reassessment_summary = {
            "total_reassessments": int(
                total_reassessments
            ),
            "concepts_reassessed": int(
                reassessment_df["concept_id"].nunique()
            ),
            "average_before_mastery": float(
                reassessment_df["before_mastery"].mean()
            ),
            "average_after_mastery": float(
                reassessment_df["after_mastery"].mean()
            ),
            "average_improvement": float(
                reassessment_df["improvement"].mean()
            )
        }

        reassessment_records = (
            reassessment_df[
                [
                    "reassessment_id",
                    "concept_id",
                    "concept_name",
                    "subject_id",
                    "before_mastery",
                    "after_mastery",
                    "improvement",
                    "created_at"
                ]
            ]
            .to_dict(orient="records")
        )

    return {
        "practice_summary": practice_summary,
        "practice_attempts": practice_records,
        "learning_progress": learning_progress_records,
        "reassessment_summary": reassessment_summary,
        "reassessments": reassessment_records
    }

def get_student_dashboard_data(student_id):

    if student_id is None:
        raise ValueError(
            "Student ID is required."
        )

    student_id = int(student_id)

    concepts_df = load_concepts()

    if concepts_df.empty:
        raise RuntimeError(
            "Concept master is empty."
        )

    with get_connection() as connection:

        student = connection.execute(
            """
            SELECT
                student_id,
                full_name,
                created_at
            FROM students
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()

        if student is None:
            raise ValueError(
                "Student not found."
            )

        assessment = connection.execute(
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
                  WHERE concept_results.assessment_id = assessments.assessment_id
              )
            ORDER BY assessment_id DESC
            LIMIT 1
            """,
            (student_id,)
        ).fetchone()

        if assessment is None:
            return {
                "student": dict(student),
                "assessment": None,
                "diagnosis": [],
                "overall_mastery": None,
                "strengths": [],
                "knowledge_gaps": [],
                "learning_priorities": [],
                "learning_path": [],
            "practice_summary": {
                "total_attempts": 0,
                "correct_attempts": 0,
                "accuracy": None,
                "average_score": None,
                "last_attempt_at": None
            },
            "practice_attempts": [],
            "learning_progress": [],
            "reassessment_summary": {
                "total_reassessments": 0,
                "concepts_reassessed": 0,
                "average_before_mastery": None,
                "average_after_mastery": None,
                "average_improvement": None
            },
            "reassessments": []
            }

        assessment_id = assessment["assessment_id"]

        concept_results = connection.execute(
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
            (assessment_id,)
        ).fetchall()

        diagnosis_df = pd.DataFrame(
            [dict(row) for row in concept_results]
        )

    if diagnosis_df.empty:
        return {
            "student": dict(student),
            "assessment": dict(assessment),
            "diagnosis": [],
            "overall_mastery": None,
            "strengths": [],
            "knowledge_gaps": [],
            "learning_priorities": [],
            "learning_path": [],
            "practice_summary": {
                "total_attempts": 0,
                "correct_attempts": 0,
                "accuracy": None,
                "average_score": None,
                "last_attempt_at": None
            },
            "practice_attempts": [],
            "learning_progress": [],
            "reassessment_summary": {
                "total_reassessments": 0,
                "concepts_reassessed": 0,
                "average_before_mastery": None,
                "average_after_mastery": None,
                "average_improvement": None
            },
            "reassessments": []
        }

    diagnosis_df["concept_id"] = (
        diagnosis_df["concept_id"].astype(int)
    )

    concepts_for_merge = concepts_df[
        [
            "concept_id",
            "concept_name",
            "subject_id",
            "difficulty",
            "prerequisites"
        ]
    ].copy()

    concepts_for_merge["concept_id"] = (
        concepts_for_merge["concept_id"].astype(int)
    )

    diagnosis_df = diagnosis_df.merge(
        concepts_for_merge,
        on="concept_id",
        how="left",
        validate="one_to_one"
    )

    if diagnosis_df["concept_name"].isna().any():
        raise RuntimeError(
            "Concept name mapping failed."
        )

    if diagnosis_df["subject_id"].isna().any():
        raise RuntimeError(
            "Subject mapping failed."
        )

    if diagnosis_df["difficulty"].isna().any():
        raise RuntimeError(
            "Difficulty mapping failed."
        )

    diagnosis_df = diagnosis_df[
        [
            "concept_id",
            "concept_name",
            "subject_id",
            "difficulty",
            "mastery",
            "gap_level",
            "gap_score",
            "prerequisites"
        ]
    ]

    overall_mastery = float(
        diagnosis_df["mastery"].mean()
    )

    strengths_df = diagnosis_df[
        diagnosis_df["gap_level"] == "Strong"
    ].copy()

    gaps_df = diagnosis_df[
        diagnosis_df["gap_level"].isin(
            ["Weak", "Critical"]
        )
    ].copy()

    priority_df = calculate_student_priority(
        diagnosis_df,
        concepts_df
    )

    if priority_df is None:
        raise RuntimeError(
            "Priority engine returned no result."
        )

    if priority_df.empty:
        raise RuntimeError(
            "Priority engine returned an empty result."
        )

    priority_required = {
        "concept_id",
        "priority_score",
        "priority_level",
        "priority_rank"
    }

    if not priority_required.issubset(
        priority_df.columns
    ):
        raise RuntimeError(
            "Priority engine output is missing required fields."
        )

    priority_display = priority_df.copy()

    # The Priority Engine receives diagnosis_df, which already contains
    # concept_name. Therefore, avoid merging concept_name a second time.
    # If concept_name is ever absent, recover it from Concept Master.

    if "concept_name" not in priority_display.columns:

        priority_display = priority_display.merge(
            concepts_for_merge[
                ["concept_id", "concept_name"]
            ],
            on="concept_id",
            how="left",
            validate="one_to_one"
        )

    if "concept_name" not in priority_display.columns:
        raise RuntimeError(
            "Priority display is missing concept_name."
        )

    if priority_display["concept_name"].isna().any():
        raise RuntimeError(
            "Priority display concept-name mapping failed."
        )

    priority_display = priority_display[
        [
            "concept_id",
            "concept_name",
            "mastery",
            "gap_level",
            "priority_score",
            "priority_level",
            "priority_rank"
        ]
    ].sort_values(
        by="priority_rank",
        ascending=True
    )

    learning_path_df = (
        build_personalized_learning_path(
            diagnosis_df,
            priority_df,
            concepts_df
        )
    )

    if learning_path_df is None:
        learning_path_df = pd.DataFrame()

    diagnosis_records = (
        diagnosis_df
        .drop(columns=["prerequisites"])
        .to_dict(orient="records")
    )

    strength_records = (
        strengths_df
        .drop(columns=["prerequisites"])
        .to_dict(orient="records")
    )

    gap_records = (
        gaps_df
        .drop(columns=["prerequisites"])
        .to_dict(orient="records")
    )

    priority_records = (
        priority_display
        .to_dict(orient="records")
    )

    learning_path_records = []

    if not learning_path_df.empty:

        learning_path_records = (
            learning_path_df
            .to_dict(orient="records")
        )

    with get_connection() as connection:

        activity_data = _get_student_activity_data(
            connection,
            student_id,
            concepts_df
        )

    return {
        "student": dict(student),
        "assessment": dict(assessment),
        "diagnosis": diagnosis_records,
        "overall_mastery": overall_mastery,
        "strengths": strength_records,
        "knowledge_gaps": gap_records,
        "learning_priorities": priority_records,
        "learning_path": learning_path_records,
        "practice_summary": activity_data["practice_summary"],
        "practice_attempts": activity_data["practice_attempts"],
        "learning_progress": activity_data["learning_progress"],
        "reassessment_summary": activity_data["reassessment_summary"],
        "reassessments": activity_data["reassessments"]
    }
