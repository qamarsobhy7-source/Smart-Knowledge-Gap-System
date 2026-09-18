"""
Synthetic data generator for the ML layer.

Generates realistic synthetic student data derived from:
    - the real question bank (270 questions, 45 concepts, 3 subjects)
    - the concept graph (prerequisites)
    - plausible student behavior patterns

The generated data is used to TRAIN and EVALUATE the ML models.

IMPORTANT:
    The data is synthetic — it is not real student data.
    All model metrics are therefore "Development Evaluation"
    and must not be presented as real-world performance.
"""

import random

import numpy as np
import pandas as pd

from .config import (
    DATA_DIR,
    RANDOM_SEED,
    SYNTHETIC_STUDENT_COUNT,
    QUESTION_TYPES,
)


# ============================================================
# LOAD REAL QUESTION BANK
# ============================================================
def load_question_bank():
    path = DATA_DIR / "final_question_bank_270.csv"
    return pd.read_csv(path)


def load_concepts():
    path = DATA_DIR / "concepts_final.csv"
    return pd.read_csv(path)


# ============================================================
# STUDENT ABILITY GENERATOR
# ============================================================
def _generate_student_ability(rng):
    """
    Generate a student's latent ability.

    Returns a dict with:
        - overall_ability     (0-1) — base skill
        - consistency         (0-1) — how stable the student is
        - speed               (0-1) — how quickly they learn
        - concept_biases      {subject_id: bias}  — natural strengths
    """
    # Distribution of student ability:
    #   - 20% struggling (0.30-0.45)
    #   - 60% average    (0.45-0.70)
    #   - 20% strong     (0.70-0.90)
    bucket = rng.random()
    if bucket < 0.20:
        overall = float(rng.uniform(0.30, 0.45))
    elif bucket < 0.80:
        overall = float(rng.uniform(0.45, 0.70))
    else:
        overall = float(rng.uniform(0.70, 0.90))

    consistency = float(rng.beta(3, 2))
    speed = float(rng.beta(2, 2))
    subject_biases = {
        1: float(rng.normal(0, 0.10)),   # Math
        2: float(rng.normal(0, 0.10)),   # Physics
        3: float(rng.normal(0, 0.10)),   # CS
    }

    return {
        "overall_ability": overall,
        "consistency": consistency,
        "speed": speed,
        "subject_biases": subject_biases,
    }


# ============================================================
# CONCEPT-LEVEL MASTERY GENERATOR
# ============================================================
def _compute_concept_mastery(student, concept_row, rng):
    """
    Compute a student's mastery on a single concept.

    Depends on:
        - student ability
        - subject bias
        - concept difficulty
        - consistency (randomness)
    """
    # Reduced difficulty penalties to get a more realistic distribution
    difficulty_map = {"Beginner": 0.05, "Intermediate": 0.12, "Advanced": 0.22}
    difficulty_penalty = difficulty_map.get(concept_row["difficulty"], 0.12)

    subject_bias = student["subject_biases"].get(int(concept_row["subject_id"]), 0)

    # Add a per-concept random affinity so students differ
    concept_affinity = float(rng.normal(0, 0.08))

    base = (
        student["overall_ability"]
        + subject_bias
        + concept_affinity
        - difficulty_penalty
    )

    noise = rng.normal(0, 0.08 * (1.0 - student["consistency"] + 0.1))

    mastery = float(np.clip(base + noise, 0.0, 1.0))
    return mastery * 100.0


# ============================================================
# QUESTION-LEVEL SCORE GENERATOR
# ============================================================
def _simulate_answer(student, concept_mastery, question_type, rng):
    """
    Simulate a student's correctness on a single question.

    Uses the concept mastery as the base probability,
    adjusted by the question type difficulty.
    """
    # Question types have different base difficulties
    type_penalty = {
        "Understanding": 0.0,
        "Application": 0.05,
        "Reasoning": 0.1,
        "Problem Solving": 0.1,
        "Misconception Detection": 0.15,
        "Transfer": 0.15,
    }.get(question_type, 0.05)

    # Probability of answering correctly
    p_correct = concept_mastery / 100.0 - type_penalty
    p_correct = float(np.clip(p_correct, 0.05, 0.98))

    return int(rng.random() < p_correct)


# ============================================================
# MAIN GENERATOR
# ============================================================
def generate_synthetic_dataset(
    n_students=SYNTHETIC_STUDENT_COUNT,
    seed=RANDOM_SEED,
):
    """
    Generate a synthetic student-level dataset.

    Returns a DataFrame with one row per (student, concept):
        Columns:
            - student_id
            - concept_id
            - concept_name
            - subject_id
            - difficulty
            - subject_grade (derived label)
            - mastery                 (0-100)
            - questions_correct       (int)
            - questions_total         (int)
            - avg_response_time       (s)
            - practice_sessions       (int)
            - reassessment_flag       (0/1)
            - improvement             (float)
            - target_status           (label: Weak / Adequate / Strong)
    """
    rng = np.random.default_rng(seed)
    random.seed(seed)

    questions_df = load_question_bank()
    concepts_df = load_concepts()

    # Group questions by concept
    questions_by_concept = {
        cid: group for cid, group in questions_df.groupby("concept_id")
    }

    rows = []

    for student_id in range(1, n_students + 1):
        student = _generate_student_ability(rng)

        # Randomly pick a subset of concepts the student was assessed on
        n_concepts = int(rng.integers(5, 16))
        concept_ids = rng.choice(
            concepts_df["concept_id"].values,
            size=n_concepts,
            replace=False,
        )

        for cid in concept_ids:
            concept_row = concepts_df[
                concepts_df["concept_id"] == cid
            ].iloc[0]

            # Concept mastery
            mastery = _compute_concept_mastery(student, concept_row, rng)

            # Simulate individual questions
            concept_questions = questions_by_concept.get(cid)
            if concept_questions is None or concept_questions.empty:
                continue

            correct = 0
            total = 0
            for _, q in concept_questions.iterrows():
                result = _simulate_answer(
                    student, mastery, q["question_type"], rng
                )
                correct += result
                total += 1

            # Response time:
            #   - moderately influenced by ability (not mastery)
            #   - plus per-question randomness
            # This avoids direct leakage from mastery.
            avg_response_time = float(
                np.clip(
                    30
                    + (1 - student["overall_ability"]) * 25
                    + rng.normal(0, 12),
                    5, 120,
                )
            )

            # Practice sessions
            practice_sessions = int(rng.integers(0, 8))

            # Reassessment (some students take reassessment)
            reassessment_flag = int(rng.random() < 0.4)

            # Improvement (only if reassessment)
            if reassessment_flag:
                # Higher speed → more improvement
                improvement = float(
                    np.clip(
                        student["speed"] * 30 + rng.normal(0, 8),
                        -10, 50,
                    )
                )
            else:
                improvement = 0.0

            # Target status from mastery
            if mastery >= 80:
                target_status = "Strong"
            elif mastery >= 60:
                target_status = "Adequate"
            elif mastery >= 40:
                target_status = "Weak"
            else:
                target_status = "Critical"

            rows.append({
                "student_id": student_id,
                "concept_id": int(cid),
                "concept_name": concept_row["concept_name"],
                "subject_id": int(concept_row["subject_id"]),
                "difficulty": concept_row["difficulty"],
                "mastery": round(mastery, 2),
                "questions_correct": int(correct),
                "questions_total": int(total),
                "accuracy": round(correct / total * 100, 2),
                "avg_response_time": round(avg_response_time, 2),
                "practice_sessions": practice_sessions,
                "reassessment_flag": reassessment_flag,
                "improvement": round(improvement, 2),
                "target_status": target_status,
            })

    df = pd.DataFrame(rows)
    return df


def save_synthetic_dataset(
    output_path=None,
    n_students=SYNTHETIC_STUDENT_COUNT,
    seed=RANDOM_SEED,
):
    """Generate and save the synthetic dataset as CSV."""
    if output_path is None:
        output_path = DATA_DIR / "synthetic_ml_training_data.csv"

    df = generate_synthetic_dataset(n_students=n_students, seed=seed)
    df.to_csv(output_path, index=False)

    print(f"✅ Synthetic dataset saved: {output_path}")
    print(f"   📊 {len(df)} rows × {len(df.columns)} columns")
    print(f"   👥 {df['student_id'].nunique()} unique students")
    print(f"   📚 {df['concept_id'].nunique()} unique concepts")
    print(f"\n📋 Target distribution:")
    print(df["target_status"].value_counts().to_string())

    return df
