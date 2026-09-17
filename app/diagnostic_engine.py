
import pandas as pd


QUESTION_TYPE_WEIGHTS = {
    "Understanding": 1 / 6,
    "Application": 1 / 6,
    "Reasoning": 1 / 6,
    "Problem Solving": 1 / 6,
    "Misconception Detection": 1 / 6,
    "Transfer": 1 / 6
}


MASTERY_THRESHOLDS = {
    "Strong": 80.0,
    "Adequate": 60.0,
    "Weak": 40.0
}


def score_question(correct_answer, student_answer):
    if pd.isna(student_answer):
        return False, 0.0

    student_answer = str(student_answer).strip().upper()
    correct_answer = str(correct_answer).strip().upper()

    is_correct = (
        student_answer == correct_answer
    )

    score = 1.0 if is_correct else 0.0

    return is_correct, score


def classify_mastery(mastery):
    mastery = float(mastery)

    if not 0.0 <= mastery <= 100.0:
        raise ValueError(
            "Mastery must be between 0 and 100."
        )

    if mastery >= MASTERY_THRESHOLDS["Strong"]:
        return "Strong"

    if mastery >= MASTERY_THRESHOLDS["Adequate"]:
        return "Adequate"

    if mastery >= MASTERY_THRESHOLDS["Weak"]:
        return "Weak"

    return "Critical"


def calculate_gap_score(mastery):
    mastery = float(mastery)

    if not 0.0 <= mastery <= 100.0:
        raise ValueError(
            "Mastery must be between 0 and 100."
        )

    return 100.0 - mastery


def calculate_concept_mastery(question_results):
    answered_weights = 0.0
    weighted_score = 0.0

    for question_type, weight in QUESTION_TYPE_WEIGHTS.items():

        score = question_results.get(
            question_type
        )

        if score is None:
            continue

        score = float(score)

        if score not in (0.0, 1.0):
            raise ValueError(
                f"Invalid score for {question_type}: {score}"
            )

        weighted_score += (
            score * weight
        )

        answered_weights += weight

    if answered_weights == 0:
        raise ValueError(
            "No answered questions available."
        )

    mastery = (
        weighted_score
        / answered_weights
    )

    return mastery * 100.0
