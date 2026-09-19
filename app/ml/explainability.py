"""
Explainability layer — SHAP-based.

Provides human-readable explanations for the ML models:

    - Risk Predictor         (why is this student at risk?)
    - Performance Predictor  (why this predicted status?)

Uses SHAP (SHapley Additive exPlanations) to attribute each
prediction to its input features.

Reference:
    Lundberg & Lee (2017) — "A Unified Approach to Interpreting
    Model Predictions" (NeurIPS)
"""

import numpy as np
import pandas as pd

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    shap = None
    SHAP_AVAILABLE = False


# ============================================================
# FRIENDLY FEATURE NAMES
# ============================================================
FEATURE_LABELS = {
    "subject_id": "Subject",
    "difficulty_encoded": "Concept Difficulty",
    "practice_sessions": "Practice Sessions",
    "avg_response_time": "Avg Response Time",
    "reassessment_flag": "Reassessment Participation",
    "improvement": "Improvement",
    "questions_correct": "Questions Correct",
    "accuracy": "Accuracy",
    "n_concepts": "Concepts Attempted",
    "avg_mastery": "Average Mastery",
    "std_mastery": "Mastery Variability",
    "total_practice": "Total Practice Sessions",
    "reassessment_rate": "Reassessment Rate",
    "avg_improvement": "Average Improvement",
    "avg_accuracy": "Average Accuracy",
}


def _humanize(feature_name):
    """Convert a raw feature name into a human-readable label."""
    return FEATURE_LABELS.get(
        feature_name,
        feature_name.replace("_", " ").title()
    )


# ============================================================
# RISK PREDICTOR EXPLANATIONS
# ============================================================
def explain_risk_prediction(model_payload, features_dict, top_k=5):
    """
    Explain a single risk prediction using SHAP.

    Args:
        model_payload: result of load_risk_predictor()
        features_dict: dict of feature values
        top_k: number of top features to return

    Returns:
        dict with:
            - base_value
            - prediction (probability of at-risk)
            - top_positive_factors  (push toward At Risk)
            - top_negative_factors  (push toward On Track)
    """
    if not SHAP_AVAILABLE:
        return {"error": "SHAP not installed."}

    model = model_payload["model"]
    feature_columns = model_payload["feature_columns"]

    row = {col: float(features_dict.get(col, 0)) for col in feature_columns}
    X = pd.DataFrame([row], columns=feature_columns)

    # TreeExplainer works for GradientBoosting
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # For binary classification, shap_values may be 2D
    if isinstance(shap_values, list):
        sv = shap_values[1][0]  # class 1 = At Risk
        base_value = float(explainer.expected_value[1])
    else:
        sv = shap_values[0] if shap_values.ndim > 1 else shap_values
        base_value = float(
            explainer.expected_value
            if np.isscalar(explainer.expected_value)
            else explainer.expected_value[0]
        )

    # Build feature contributions
    contributions = []
    for i, col in enumerate(feature_columns):
        contributions.append({
            "feature": col,
            "label": _humanize(col),
            "value": float(row[col]),
            "shap_value": float(sv[i]),
        })

    # Sort by absolute impact
    contributions.sort(key=lambda x: -abs(x["shap_value"]))

    positives = [c for c in contributions if c["shap_value"] > 0][:top_k]
    negatives = [c for c in contributions if c["shap_value"] < 0][:top_k]

    # Prediction
    pred_proba = float(model.predict_proba(X)[0][1])

    return {
        "base_value": base_value,
        "prediction": pred_proba,
        "top_positive_factors": positives,
        "top_negative_factors": negatives,
        "all_contributions": contributions,
    }


# ============================================================
# PERFORMANCE PREDICTOR EXPLANATIONS
# ============================================================
def explain_performance_prediction(model_payload, features_dict, top_k=5):
    """
    Explain a single performance prediction using SHAP.

    Args:
        model_payload: result of load_performance_predictor()
        features_dict: dict of feature values
        top_k: number of top features

    Returns:
        dict with top feature contributions and probabilities.
    """
    if not SHAP_AVAILABLE:
        return {"error": "SHAP not installed."}

    model = model_payload["model"]
    label_encoder = model_payload["label_encoder"]
    feature_columns = model_payload["feature_columns"]

    row = {col: float(features_dict.get(col, 0)) for col in feature_columns}
    X = pd.DataFrame([row], columns=feature_columns)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Predict
    proba = model.predict_proba(X)[0]
    pred_idx = int(np.argmax(proba))
    predicted_status = label_encoder.inverse_transform([pred_idx])[0]

    # Get contributions for the predicted class
    if isinstance(shap_values, list):
        sv = shap_values[pred_idx][0]
        base = explainer.expected_value
        base_value = (
            float(base[pred_idx]) if hasattr(base, "__len__") else float(base)
        )
    elif hasattr(shap_values, "shape") and len(shap_values.shape) == 3:
        sv = shap_values[0, :, pred_idx]
        base = explainer.expected_value
        base_value = (
            float(base[pred_idx]) if hasattr(base, "__len__") else float(base)
        )
    else:
        sv = shap_values[0] if shap_values.ndim > 1 else shap_values
        base_value = float(
            explainer.expected_value
            if np.isscalar(explainer.expected_value)
            else explainer.expected_value[0]
        )

    contributions = []
    for i, col in enumerate(feature_columns):
        contributions.append({
            "feature": col,
            "label": _humanize(col),
            "value": float(row[col]),
            "shap_value": float(sv[i]),
        })

    contributions.sort(key=lambda x: -abs(x["shap_value"]))

    return {
        "predicted_status": predicted_status,
        "probabilities": {
            label_encoder.inverse_transform([i])[0]: float(p)
            for i, p in enumerate(proba)
        },
        "base_value": base_value,
        "top_contributions": contributions[:top_k],
        "all_contributions": contributions,
    }


# ============================================================
# TEXT SUMMARY GENERATOR
# ============================================================
def generate_explanation_text(explanation, task="risk"):
    """
    Turn a SHAP explanation into a natural-language summary.

    This makes the AI output more accessible to non-technical users.
    """
    if not explanation or "error" in explanation:
        return "Explanation unavailable."

    if task == "risk":
        pred = explanation["prediction"]
        status = "At Risk" if pred > 0.5 else "On Track"
        confidence = max(pred, 1 - pred) * 100

        positives = explanation["top_positive_factors"]
        negatives = explanation["top_negative_factors"]

        lines = [
            f"Prediction: {status} (confidence: {confidence:.1f}%)",
            "",
        ]

        if positives:
            lines.append("🔴 Factors pushing toward AT RISK:")
            for f in positives[:3]:
                lines.append(
                    f"   • {f['label']} = {f['value']:.2f} "
                    f"(impact: +{f['shap_value']:.3f})"
                )

        if negatives:
            lines.append("")
            lines.append("🟢 Factors pushing toward ON TRACK:")
            for f in negatives[:3]:
                lines.append(
                    f"   • {f['label']} = {f['value']:.2f} "
                    f"(impact: {f['shap_value']:.3f})"
                )

        return "\n".join(lines)

    if task == "performance":
        status = explanation["predicted_status"]
        proba = explanation["probabilities"]

        lines = [
            f"Predicted Status: {status}",
            "",
            "Probabilities:",
        ]
        for cls, p in sorted(proba.items(), key=lambda x: -x[1]):
            lines.append(f"   • {cls}: {p * 100:.1f}%")

        lines.append("")
        lines.append("Top contributing factors:")
        for f in explanation["top_contributions"][:3]:
            direction = "+" if f["shap_value"] > 0 else ""
            lines.append(
                f"   • {f['label']} = {f['value']:.2f} "
                f"(impact: {direction}{f['shap_value']:.3f})"
            )

        return "\n".join(lines)

    return "Explanation unavailable."
