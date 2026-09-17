
import pandas as pd

try:
    from .database import (
        create_student,
        create_assessment,
        save_answer,
        save_concept_result
    )
except ImportError:
    from database import (
        create_student,
        create_assessment,
        save_answer,
        save_concept_result
    )

try:
    from .repository import (
        load_question_bank,
        load_concepts
    )
except ImportError:
    from repository import (
        load_question_bank,
        load_concepts
    )

try:
    from .diagnostic_engine import (
        score_question,
        calculate_concept_mastery,
        classify_mastery,
        calculate_gap_score
    )
except ImportError:
    from diagnostic_engine import (
        score_question,
        calculate_concept_mastery,
        classify_mastery,
        calculate_gap_score
    )

try:
    from .priority_engine import (
        calculate_student_priority
    )
except ImportError:
    from priority_engine import (
        calculate_student_priority
    )

try:
    from .learning_path_engine import (
        build_personalized_learning_path
    )
except ImportError:
    from learning_path_engine import (
        build_personalized_learning_path
    )


class BackendService:

    def __init__(
        self,
        question_bank_df=None,
        concepts_df=None
    ):

        if question_bank_df is None:
            question_bank_df = (
                load_question_bank()
            )

        if concepts_df is None:
            concepts_df = (
                load_concepts()
            )

        self.question_bank = (
            question_bank_df.copy()
        )

        self.concepts = (
            concepts_df.copy()
        )

        self._validate_data()

    # --------------------------------------------------------
    # DATA VALIDATION
    # --------------------------------------------------------

    def _validate_data(self):

        required_questions = {
            "question_id",
            "concept_id",
            "correct_answer"
        }

        required_concepts = {
            "concept_id",
            "concept_name",
            "subject_id",
            "difficulty",
            "prerequisites"
        }

        missing_questions = (
            required_questions
            - set(self.question_bank.columns)
        )

        if missing_questions:
            raise ValueError(
                "Missing question columns: "
                f"{sorted(missing_questions)}"
            )

        missing_concepts = (
            required_concepts
            - set(self.concepts.columns)
        )

        if missing_concepts:
            raise ValueError(
                "Missing concept columns: "
                f"{sorted(missing_concepts)}"
            )

        if len(self.question_bank) != 270:
            raise ValueError(
                "Question bank must contain "
                "exactly 270 questions."
            )

        if len(self.concepts) != 45:
            raise ValueError(
                "Concept master must contain "
                "exactly 45 concepts."
            )

        if (
            self.question_bank["question_id"]
            .nunique()
            != 270
        ):
            raise ValueError(
                "Question IDs must be unique."
            )

        if (
            self.concepts["concept_id"]
            .nunique()
            != 45
        ):
            raise ValueError(
                "Concept IDs must be unique."
            )

        question_concepts = set(
            self.question_bank[
                "concept_id"
            ].astype(int)
        )

        concept_ids = set(
            self.concepts[
                "concept_id"
            ].astype(int)
        )

        if not question_concepts.issubset(
            concept_ids
        ):
            raise ValueError(
                "Question bank contains "
                "unknown concept IDs."
            )

    # --------------------------------------------------------
    # STUDENT CREATION
    # --------------------------------------------------------

    def register_student(
        self,
        full_name
    ):

        return create_student(
            full_name
        )

    # --------------------------------------------------------
    # ASSESSMENT CREATION
    # --------------------------------------------------------

    def start_assessment(
        self,
        student_id,
        assessment_type="Diagnostic"
    ):

        return create_assessment(
            student_id,
            assessment_type
        )

    # --------------------------------------------------------
    # QUESTION SCORING
    # --------------------------------------------------------

    def score_answer(
        self,
        question_id,
        student_answer
    ):

        matches = self.question_bank[
            self.question_bank[
                "question_id"
            ].astype(str)
            == str(question_id)
        ]

        if len(matches) != 1:
            raise ValueError(
                "Question ID not found or duplicated: "
                f"{question_id}"
            )

        question = matches.iloc[0]

        is_correct, score = score_question(
            question["correct_answer"],
            student_answer
        )

        return {
            "question_id": question_id,
            "concept_id": int(
                question["concept_id"]
            ),
            "is_correct": bool(
                is_correct
            ),
            "score": float(score)
        }
    def persist_answer(
        self,
        assessment_id,
        student_answer_result,
        student_answer
    ):
        if not isinstance(student_answer_result, dict):
            raise ValueError(
                "student_answer_result must be a dictionary."
            )

        required_keys = {
            "question_id",
            "is_correct",
            "score"
        }

        if not required_keys.issubset(
            student_answer_result.keys()
        ):
            raise ValueError(
                "student_answer_result is missing required fields."
            )

        return save_answer(
            assessment_id=assessment_id,
            question_id=student_answer_result["question_id"],
            student_answer=student_answer,
            is_correct=student_answer_result["is_correct"],
            score=student_answer_result["score"]
        )


    # --------------------------------------------------------
    # CONCEPT MASTERY
    # --------------------------------------------------------

    def calculate_mastery(
        self,
        concept_id,
        answers_df
    ):

        concept_id = int(
            concept_id
        )

        concept_questions = (
            self.question_bank[
                self.question_bank[
                    "concept_id"
                ].astype(int)
                == concept_id
            ]
        )

        if concept_questions.empty:
            raise ValueError(
                f"Unknown concept_id: {concept_id}"
            )

        merged = concept_questions.merge(
            answers_df[
                [
                    "question_id",
                    "is_correct",
                    "score"
                ]
            ],
            on="question_id",
            how="left"
        )

        if "question_type" not in merged.columns:
            raise ValueError(
                "Question bank must contain "
                "question_type for mastery calculation."
            )

        answered = merged[
            merged["score"].notna()
        ].copy()

        if answered.empty:
            raise ValueError(
                "No answered questions available."
            )

        question_type_scores = (
            answered
            .groupby("question_type")["score"]
            .mean()
            .to_dict()
        )

        mastery = calculate_concept_mastery(
            question_type_scores
        )

        gap_level = classify_mastery(
            mastery
        )

        gap_score = calculate_gap_score(
            mastery
        )

        return {
            "concept_id": concept_id,
            "mastery": float(mastery),
            "gap_level": gap_level,
            "gap_score": float(gap_score)
        }

    # --------------------------------------------------------
    # SAVE CONCEPT RESULT
    # --------------------------------------------------------

    def persist_concept_result(
        self,
        assessment_id,
        concept_result
    ):

        return save_concept_result(
            assessment_id=assessment_id,
            concept_id=concept_result[
                "concept_id"
            ],
            mastery=concept_result[
                "mastery"
            ],
            gap_level=concept_result[
                "gap_level"
            ],
            gap_score=concept_result[
                "gap_score"
            ]
        )

    # --------------------------------------------------------
    # STUDENT PRIORITY
    # --------------------------------------------------------

    def build_priority(
        self,
        diagnosis_df
    ):

        priority_df = (
            calculate_student_priority(
                diagnosis_df,
                self.concepts
            )
        )

        return priority_df

    # --------------------------------------------------------
    # PERSONALIZED LEARNING PATH
    # --------------------------------------------------------

    def build_learning_path(
        self,
        diagnosis_df,
        priority_df
    ):

        return build_personalized_learning_path(
            diagnosis_df=diagnosis_df,
            priority_df=priority_df,
            concepts_df=self.concepts
        )
