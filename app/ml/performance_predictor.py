"""
Student Performance Predictor.

Predicts a student's target mastery status
(Critical / Weak / Adequate / Strong) based on:

    - subject
    - concept difficulty
    - practice sessions
    - response time
    - reassessment participation
    - improvement

Model: Random Forest Classifier
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from .config import (
    METRICS_DIR,
    PERFORMANCE_MODEL_PATH,
    RANDOM_SEED,
)


FEATURE_COLUMNS = [
    "subject_id",
    "difficulty_encoded",
    "practice_sessions",
    "accuracy",
    "reassessment_flag",
    "improvement",
]

DIFFICULTY_ENCODING = {
    "Beginner": 0,
    "Intermediate": 1,
    "Advanced": 2,
}

CLASS_ORDER = ["Critical", "Weak", "Adequate", "Strong"]


def _prepare_features(df):
    """Convert raw columns into numeric features."""
    df = df.copy()
    df["difficulty_encoded"] = df["difficulty"].map(DIFFICULTY_ENCODING)
    df = df.dropna(subset=["difficulty_encoded"])

    X = df[FEATURE_COLUMNS].astype(float)
    return X, df


def train_performance_predictor(df, verbose=True):
    """
    Train a Random Forest classifier on the synthetic dataset.

    Returns:
        dict with model, label_encoder, metrics
    """
    X, df = _prepare_features(df)
    y_raw = df["target_status"]

    label_encoder = LabelEncoder()
    label_encoder.fit(CLASS_ORDER)
    y = label_encoder.transform(y_raw)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    metrics = {
        "task": "classification",
        "model": "RandomForestClassifier",
        "purpose": "Student Performance Prediction",
        "evaluation_type": "Development Evaluation",
        "synthetic_data": True,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision_macro": float(
            precision_score(y_test, y_pred, average="macro", zero_division=0)
        ),
        "recall_macro": float(
            recall_score(y_test, y_pred, average="macro", zero_division=0)
        ),
        "f1_macro": float(
            f1_score(y_test, y_pred, average="macro", zero_division=0)
        ),
        "f1_weighted": float(
            f1_score(y_test, y_pred, average="weighted", zero_division=0)
        ),
        "classes": CLASS_ORDER,
        "per_class_report": classification_report(
            y_test, y_pred,
            target_names=CLASS_ORDER,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "feature_importance": dict(
            zip(FEATURE_COLUMNS, model.feature_importances_.tolist())
        ),
    }

    if verbose:
        print("=" * 60)
        print("📊 Student Performance Predictor — Metrics")
        print("=" * 60)
        print(f"   Accuracy:        {metrics['accuracy']:.4f}")
        print(f"   Precision (macro): {metrics['precision_macro']:.4f}")
        print(f"   Recall (macro):    {metrics['recall_macro']:.4f}")
        print(f"   F1 (macro):        {metrics['f1_macro']:.4f}")
        print(f"   F1 (weighted):     {metrics['f1_weighted']:.4f}")
        print()
        print("📋 Classification Report:")
        print(classification_report(
            y_test, y_pred,
            target_names=CLASS_ORDER,
            zero_division=0,
        ))
        print("📋 Feature Importance:")
        for name, value in sorted(
            metrics["feature_importance"].items(),
            key=lambda x: -x[1],
        ):
            print(f"   {name:25s} {value:.4f}")

    return {
        "model": model,
        "label_encoder": label_encoder,
        "metrics": metrics,
        "feature_columns": FEATURE_COLUMNS,
    }


def save_performance_predictor(trained):
    """Save the trained model and its metrics."""
    PERFORMANCE_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": trained["model"],
            "label_encoder": trained["label_encoder"],
            "feature_columns": trained["feature_columns"],
        },
        PERFORMANCE_MODEL_PATH,
    )

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = METRICS_DIR / "performance_predictor_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(trained["metrics"], f, indent=2)

    print(f"\n✅ Model saved: {PERFORMANCE_MODEL_PATH}")
    print(f"✅ Metrics saved: {metrics_path}")


def load_performance_predictor():
    """Load the trained model from disk."""
    if not PERFORMANCE_MODEL_PATH.exists():
        return None

    payload = joblib.load(PERFORMANCE_MODEL_PATH)
    return payload


def predict_status(model_payload, features_dict):
    """
    Predict the target status for a single student/concept.

    Args:
        model_payload: result of load_performance_predictor()
        features_dict: dict with keys matching FEATURE_COLUMNS

    Returns:
        dict with predicted_status, probabilities
    """
    model = model_payload["model"]
    label_encoder = model_payload["label_encoder"]

    feature_columns = model_payload["feature_columns"]
    row = {col: float(features_dict.get(col, 0)) for col in feature_columns}
    import pandas as pd
    x = pd.DataFrame([row], columns=feature_columns)

    pred = model.predict(x)[0]
    proba = model.predict_proba(x)[0]

    predicted_status = label_encoder.inverse_transform([pred])[0]

    return {
        "predicted_status": predicted_status,
        "probabilities": {
            label_encoder.inverse_transform([i])[0]: float(p)
            for i, p in enumerate(proba)
        },
    }
