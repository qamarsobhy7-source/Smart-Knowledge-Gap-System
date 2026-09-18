"""
Student Risk Predictor — Binary classification.

Predicts whether a student is "At Risk" on a concept.

Target:
    At Risk   = mastery < 60   (Critical + Weak)
    On Track  = mastery >= 60  (Adequate + Strong)

This binary formulation is more robust than 4-class classification
for small / synthetic datasets.
"""

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from .config import MODELS_DIR, RANDOM_SEED


RISK_MODEL_PATH = MODELS_DIR / "student_risk_model.joblib"

FEATURE_COLUMNS = [
    "subject_id",
    "difficulty_encoded",
    "practice_sessions",
    "avg_response_time",
    "reassessment_flag",
    "improvement",
    "questions_correct",
]

DIFFICULTY_ENCODING = {
    "Beginner": 0,
    "Intermediate": 1,
    "Advanced": 2,
}


def _prepare(df):
    df = df.copy()
    df["difficulty_encoded"] = df["difficulty"].map(DIFFICULTY_ENCODING)
    df = df.dropna(subset=["difficulty_encoded"])

    # Binary target
    df["is_at_risk"] = (df["mastery"] < 60.0).astype(int)

    X = df[FEATURE_COLUMNS].astype(float)
    y = df["is_at_risk"].values

    return X, y, df


def train_risk_predictor(df, verbose=True):
    X, y, _ = _prepare(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    model = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        random_state=RANDOM_SEED,
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "task": "binary_classification",
        "model": "GradientBoostingClassifier",
        "purpose": "Student Risk Prediction (At Risk / On Track)",
        "evaluation_type": "Development Evaluation",
        "synthetic_data": True,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "feature_importance": dict(
            zip(FEATURE_COLUMNS, model.feature_importances_.tolist())
        ),
    }

    if verbose:
        print("=" * 60)
        print("🎯 Student Risk Predictor — Metrics")
        print("=" * 60)
        print(f"   Accuracy:   {metrics['accuracy']:.4f}")
        print(f"   Precision:  {metrics['precision']:.4f}")
        print(f"   Recall:     {metrics['recall']:.4f}")
        print(f"   F1:         {metrics['f1']:.4f}")
        print(f"   ROC-AUC:    {metrics['roc_auc']:.4f}")
        print()
        print(classification_report(
            y_test, y_pred,
            target_names=["On Track", "At Risk"],
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
        "metrics": metrics,
        "feature_columns": FEATURE_COLUMNS,
    }


def save_risk_predictor(trained):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": trained["model"],
            "feature_columns": trained["feature_columns"],
        },
        RISK_MODEL_PATH,
    )

    metrics_dir = MODELS_DIR / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    with open(metrics_dir / "risk_predictor_metrics.json", "w", encoding="utf-8") as f:
        json.dump(trained["metrics"], f, indent=2)

    print(f"\n✅ Model saved: {RISK_MODEL_PATH}")
    print(f"✅ Metrics saved: {metrics_dir / 'risk_predictor_metrics.json'}")


def load_risk_predictor():
    if not RISK_MODEL_PATH.exists():
        return None
    return joblib.load(RISK_MODEL_PATH)


def predict_risk(model_payload, features_dict):
    model = model_payload["model"]
    feature_columns = model_payload["feature_columns"]

    # Build a DataFrame with the correct column names to avoid warnings
    row = {col: float(features_dict.get(col, 0)) for col in feature_columns}
    import pandas as pd
    x = pd.DataFrame([row], columns=feature_columns)

    pred = model.predict(x)[0]
    proba = model.predict_proba(x)[0]

    return {
        "is_at_risk": bool(pred),
        "risk_probability": float(proba[1]),
        "on_track_probability": float(proba[0]),
    }
