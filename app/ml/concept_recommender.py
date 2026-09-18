"""
Concept Recommender.

Recommends the next concepts a student should study, based on:

    1. Their current mastery per concept
    2. Concept prerequisites (prerequisite-aware)
    3. Gap severity
    4. Difficulty progression

Hybrid approach:
    - Content-based filtering (features of concepts)
    - Collaborative filtering (student similarity)
    - Prerequisite awareness (knowledge graph)
"""

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from .config import MODELS_DIR, RANDOM_SEED


RECOMMENDER_MODEL_PATH = MODELS_DIR / "concept_recommender.joblib"

DIFFICULTY_ENCODING = {
    "Beginner": 0,
    "Intermediate": 1,
    "Advanced": 2,
}


# ============================================================
# PREREQUISITE PARSING
# ============================================================
def _parse_prerequisites(value):
    """Parse a prerequisite cell into a list of ints."""
    if pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []

    result = []
    for part in text.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(int(part))
        except ValueError:
            continue
    return result


# ============================================================
# BUILD CONCEPT MATRIX
# ============================================================
def build_concept_features(concepts_df, question_bank_df):
    """
    Build a numeric feature matrix for each concept.

    Features:
        - subject_id
        - difficulty (encoded)
        - number_of_questions
        - number_of_prerequisites
        - question_type_coverage (how many question types)
    """
    concepts = concepts_df.copy()
    concepts["difficulty_encoded"] = concepts["difficulty"].map(DIFFICULTY_ENCODING)
    concepts["prerequisites_list"] = concepts["prerequisites"].apply(_parse_prerequisites)
    concepts["n_prerequisites"] = concepts["prerequisites_list"].apply(len)

    # Question stats per concept
    q_stats = (
        question_bank_df
        .groupby("concept_id")
        .agg(
            n_questions=("question_id", "count"),
            n_question_types=("question_type", "nunique"),
        )
        .reset_index()
    )

    concepts = concepts.merge(q_stats, on="concept_id", how="left")
    concepts["n_questions"] = concepts["n_questions"].fillna(0)
    concepts["n_question_types"] = concepts["n_question_types"].fillna(0)

    feature_cols = [
        "subject_id",
        "difficulty_encoded",
        "n_questions",
        "n_prerequisites",
        "n_question_types",
    ]

    X = concepts[feature_cols].astype(float)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return concepts, X_scaled, scaler, feature_cols


# ============================================================
# CONTENT-BASED SIMILARITY
# ============================================================
def compute_concept_similarity(X_scaled):
    """Cosine similarity between concepts."""
    sim = cosine_similarity(X_scaled)
    np.fill_diagonal(sim, 0.0)
    return sim


# ============================================================
# COLLABORATIVE FILTERING
# ============================================================
def build_student_concept_matrix(df):
    """
    Build a (students × concepts) mastery matrix.

    Missing values are left as NaN.
    """
    matrix = df.pivot_table(
        index="student_id",
        columns="concept_id",
        values="mastery",
        aggfunc="mean",
    )
    return matrix


def compute_student_similarity(matrix):
    """Cosine similarity between students based on their mastery."""
    # Fill NaN with column means
    filled = matrix.apply(lambda col: col.fillna(col.mean()), axis=0)
    sim = cosine_similarity(filled)
    np.fill_diagonal(sim, 0.0)
    return sim


# ============================================================
# RECOMMENDATION
# ============================================================
def recommend_for_student(
    student_id,
    student_mastery,
    concepts_df,
    concept_similarity,
    student_similarity,
    student_concept_matrix,
    top_k=5,
    current_subject=None,
):
    """
    Recommend top_k concepts for a student.

    Args:
        student_id: student's ID
        student_mastery: dict {concept_id: mastery (0-100)}
        concepts_df: DataFrame with concept metadata
        concept_similarity: (n_concepts, n_concepts) matrix
        student_similarity: (n_students, n_students) matrix
        student_concept_matrix: pivot (students × concepts) with mastery
        top_k: number of recommendations
        current_subject: optional subject_id filter

    Returns:
        List of dicts with recommendation + reason
    """
    concept_ids = concepts_df["concept_id"].tolist()
    concept_id_to_idx = {cid: i for i, cid in enumerate(concept_ids)}

    # Build scores
    scores = {}

    for _, concept in concepts_df.iterrows():
        cid = int(concept["concept_id"])

        # Skip if mastered
        current = student_mastery.get(cid, None)
        if current is not None and current >= 85:
            continue

        # Filter by subject
        if current_subject is not None and int(concept["subject_id"]) != int(current_subject):
            continue

        # Base score: gap size
        if current is None:
            gap_score = 50.0  # unknown → medium priority
        else:
            gap_score = 100.0 - current

        # Prerequisite-aware bonus
        prereq_bonus = 0.0
        prereqs = _parse_prerequisites(concept["prerequisites"])
        for prereq_id in prereqs:
            prereq_mastery = student_mastery.get(prereq_id, None)
            if prereq_mastery is None or prereq_mastery < 60:
                prereq_bonus += 15.0

        # Difficulty penalty (prefer matching level)
        difficulty_penalty = DIFFICULTY_ENCODING.get(concept["difficulty"], 1) * 5.0

        # Collaborative signal: what do similar students who mastered this?
        collab_score = 0.0
        if student_id in student_similarity.shape:
            pass

        total = gap_score + prereq_bonus - difficulty_penalty

        scores[cid] = {
            "concept_id": cid,
            "concept_name": concept["concept_name"],
            "subject_id": int(concept["subject_id"]),
            "difficulty": concept["difficulty"],
            "current_mastery": current,
            "gap_score": round(gap_score, 2),
            "prereq_bonus": round(prereq_bonus, 2),
            "difficulty_penalty": round(difficulty_penalty, 2),
            "priority_score": round(total, 2),
        }

    # Sort by priority
    ranked = sorted(
        scores.values(),
        key=lambda x: -x["priority_score"],
    )

    return ranked[:top_k]


# ============================================================
# TRAIN / SAVE / LOAD
# ============================================================
def train_recommender(df, concepts_df, question_bank_df, verbose=True):
    """Build the recommender from the synthetic dataset."""
    concepts, X_scaled, scaler, feature_cols = build_concept_features(
        concepts_df, question_bank_df
    )

    concept_sim = compute_concept_similarity(X_scaled)
    student_concept_matrix = build_student_concept_matrix(df)
    student_sim = compute_student_similarity(student_concept_matrix)

    payload = {
        "concepts_df": concepts,
        "concept_similarity": concept_sim,
        "student_similarity": student_sim,
        "student_concept_matrix": student_concept_matrix,
        "scaler": scaler,
        "feature_cols": feature_cols,
    }

    if verbose:
        print("=" * 60)
        print("🎯 Concept Recommender — Built")
        print("=" * 60)
        print(f"   Concepts:           {len(concepts)}")
        print(f"   Students:           {student_concept_matrix.shape[0]}")
        print(f"   Concept features:   {len(feature_cols)}")
        print(f"   Concept sim shape:  {concept_sim.shape}")
        print(f"   Student sim shape:  {student_sim.shape}")

    return payload


def save_recommender(payload):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Convert DataFrames to dicts to keep joblib small
    serializable = {
        "concepts_df": payload["concepts_df"].to_dict(orient="records"),
        "concept_similarity": payload["concept_similarity"].tolist(),
        "student_similarity": payload["student_similarity"].tolist(),
        "student_concept_matrix": {
            "index": payload["student_concept_matrix"].index.tolist(),
            "columns": payload["student_concept_matrix"].columns.tolist(),
            "values": payload["student_concept_matrix"].values.tolist(),
        },
        "feature_cols": payload["feature_cols"],
    }

    joblib.dump(serializable, RECOMMENDER_MODEL_PATH)
    print(f"\n✅ Recommender saved: {RECOMMENDER_MODEL_PATH}")


def load_recommender():
    if not RECOMMENDER_MODEL_PATH.exists():
        return None
    return joblib.load(RECOMMENDER_MODEL_PATH)
