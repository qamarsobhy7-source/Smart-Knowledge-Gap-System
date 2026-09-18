"""
ML Service — high-level interface to all ML models.

Provides a single entry point for the Flask app to:
    - predict student risk
    - predict target status
    - recommend concepts
    - assign student clusters
    - retrieve model metrics

Loads models lazily (once per process) and caches them.
"""

import json
from pathlib import Path

from .config import MODELS_DIR, METRICS_DIR


# ============================================================
# LAZY MODEL LOADING
# ============================================================
_models = {
    "risk": None,
    "performance": None,
    "recommender": None,
    "clusterer": None,
}


def _load_risk():
    if _models["risk"] is None:
        from .risk_predictor import load_risk_predictor
        _models["risk"] = load_risk_predictor()
    return _models["risk"]


def _load_performance():
    if _models["performance"] is None:
        from .performance_predictor import load_performance_predictor
        _models["performance"] = load_performance_predictor()
    return _models["performance"]


def _load_recommender():
    if _models["recommender"] is None:
        from .concept_recommender import load_recommender
        _models["recommender"] = load_recommender()
    return _models["recommender"]


def _load_clusterer():
    if _models["clusterer"] is None:
        from .student_clusterer import load_clusterer
        _models["clusterer"] = load_clusterer()
    return _models["clusterer"]


# ============================================================
# PUBLIC API
# ============================================================
def models_available():
    """Return a dict of which models are loaded on disk."""
    return {
        "risk": (MODELS_DIR / "student_risk_model.joblib").exists(),
        "performance": (MODELS_DIR / "student_performance_model.joblib").exists(),
        "recommender": (MODELS_DIR / "concept_recommender.joblib").exists(),
        "clusterer": (MODELS_DIR / "student_clusterer.joblib").exists(),
        "knowledge_tracing": (MODELS_DIR / "knowledge_tracing_model.pt").exists(),
    }


def predict_student_risk(features):
    """
    Predict whether a student is at risk on a concept.

    Args:
        features: dict with keys:
            subject_id, difficulty_encoded, practice_sessions,
            avg_response_time, reassessment_flag, improvement,
            questions_correct

    Returns:
        dict or None if model is missing
    """
    payload = _load_risk()
    if payload is None:
        return None

    from .risk_predictor import predict_risk
    return predict_risk(payload, features)


def predict_student_performance(features):
    """
    Predict the target mastery status (Critical/Weak/Adequate/Strong).
    """
    payload = _load_performance()
    if payload is None:
        return None

    from .performance_predictor import predict_status
    return predict_status(payload, features)


def recommend_concepts(
    student_id,
    student_mastery,
    concepts_df,
    top_k=5,
    current_subject=None,
):
    """
    Recommend top_k concepts for a student.

    Args:
        student_id: int
        student_mastery: dict {concept_id: mastery (0-100)}
        concepts_df: pandas DataFrame with concept metadata
        top_k: number of recommendations
        current_subject: optional subject_id filter

    Returns:
        list of recommendation dicts, or empty list if model is missing
    """
    payload = _load_recommender()
    if payload is None:
        return []

    from .concept_recommender import recommend_for_student
    import numpy as np
    import pandas as pd

    # Rebuild DataFrame from list of dicts
    concepts_df_local = pd.DataFrame(payload["concepts_df"])

    concept_sim = np.array(payload["concept_similarity"])
    student_sim = np.array(payload["student_similarity"])

    # Rebuild the student-concept matrix
    matrix_info = payload["student_concept_matrix"]
    matrix = pd.DataFrame(
        matrix_info["values"],
        index=matrix_info["index"],
        columns=matrix_info["columns"],
    )

    return recommend_for_student(
        student_id=student_id,
        student_mastery=student_mastery,
        concepts_df=concepts_df_local,
        concept_similarity=concept_sim,
        student_similarity=student_sim,
        student_concept_matrix=matrix,
        top_k=top_k,
        current_subject=current_subject,
    )


def predict_student_cluster(features):
    """
    Assign a student to a cluster.

    Args:
        features: dict with keys matching the clusterer's feature_cols.

    Returns:
        dict or None if model is missing
    """
    payload = _load_clusterer()
    if payload is None:
        return None

    from .student_clusterer import predict_cluster
    return predict_cluster(payload, features)


# ============================================================
# KNOWLEDGE TRACING
# ============================================================
_models["knowledge_tracing"] = None


def _load_knowledge_tracing():
    if _models["knowledge_tracing"] is None:
        from .knowledge_tracing import load_knowledge_tracing
        _models["knowledge_tracing"] = load_knowledge_tracing()
    return _models["knowledge_tracing"]


def predict_next_correctness(history_concepts, history_correct):
    """
    Predict probability of correct answer on the NEXT concept.

    Args:
        history_concepts: list of concept IDs the student attempted
        history_correct: list of 0/1 correctness per attempt

    Returns:
        dict with probability, or None if model missing
    """
    kt_model = _load_knowledge_tracing()
    if kt_model is None:
        return None

    from .knowledge_tracing import predict_next_correctness as _predict
    prob = _predict(kt_model, history_concepts, history_correct)

    return {
        "next_correct_probability": float(prob),
        "history_length": len(history_concepts),
    }


# ============================================================
# EXPLAINABLE AI (SHAP)
# ============================================================
def explain_risk(features):
    """
    Explain a single risk prediction using SHAP.

    Returns:
        dict with top positive/negative factors + text summary,
        or None if model or SHAP is missing.
    """
    payload = _load_risk()
    if payload is None:
        return None

    from .explainability import (
        explain_risk_prediction,
        generate_explanation_text,
    )

    explanation = explain_risk_prediction(payload, features)
    if explanation and "error" not in explanation:
        explanation["text_summary"] = generate_explanation_text(
            explanation, task="risk"
        )
    return explanation


def explain_performance(features):
    """
    Explain a single performance prediction using SHAP.

    Returns:
        dict with top contributions + text summary,
        or None if model or SHAP is missing.
    """
    payload = _load_performance()
    if payload is None:
        return None

    from .explainability import (
        explain_performance_prediction,
        generate_explanation_text,
    )

    explanation = explain_performance_prediction(payload, features)
    if explanation and "error" not in explanation:
        explanation["text_summary"] = generate_explanation_text(
            explanation, task="performance"
        )
    return explanation


def get_model_metrics():
    """Load all metrics JSON files from disk."""
    metrics = {}

    files = {
        "risk_predictor": METRICS_DIR / "risk_predictor_metrics.json",
        "performance_predictor": METRICS_DIR / "performance_predictor_metrics.json",
        "clusterer": METRICS_DIR / "clusterer_metrics.json",
    }

    for name, path in files.items():
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    metrics[name] = json.load(f)
            except Exception:
                pass

    return metrics
