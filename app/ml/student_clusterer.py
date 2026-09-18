"""
Student Clusterer.

Groups students into interpretable clusters using K-Means,
with PCA for 2D visualization.

Features per student:
    - avg mastery
    - std mastery
    - avg response time
    - total practice sessions
    - reassessment participation rate
    - improvement mean
    - accuracy mean
"""

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from .config import MODELS_DIR, RANDOM_SEED


CLUSTERER_MODEL_PATH = MODELS_DIR / "student_clusterer.joblib"

# Human-readable labels for each cluster (assigned after fitting)
CLUSTER_LABELS = [
    "High Performers",
    "Steady Learners",
    "Struggling Students",
    "Improving Students",
    "At-Risk Students",
]


# ============================================================
# BUILD STUDENT FEATURES
# ============================================================
def build_student_features(df):
    """
    Aggregate per-concept rows into one row per student.
    """
    features = (
        df
        .groupby("student_id")
        .agg(
            avg_mastery=("mastery", "mean"),
            std_mastery=("mastery", "std"),
            avg_response_time=("avg_response_time", "mean"),
            total_practice=("practice_sessions", "sum"),
            reassessment_rate=("reassessment_flag", "mean"),
            avg_improvement=("improvement", "mean"),
            avg_accuracy=("accuracy", "mean"),
            n_concepts=("concept_id", "count"),
        )
        .reset_index()
    )

    features["std_mastery"] = features["std_mastery"].fillna(0.0)
    return features


# ============================================================
# CLUSTERING
# ============================================================
def train_clusterer(df, n_clusters=4, verbose=True):
    features = build_student_features(df)

    feature_cols = [
        "avg_mastery",
        "std_mastery",
        "avg_response_time",
        "total_practice",
        "reassessment_rate",
        "avg_improvement",
        "avg_accuracy",
        "n_concepts",
    ]

    X = features[feature_cols].astype(float)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Fit K-Means
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=RANDOM_SEED,
        n_init=10,
    )
    labels = kmeans.fit_predict(X_scaled)

    # Silhouette score
    sil = float(silhouette_score(X_scaled, labels))

    # PCA for 2D visualization
    pca = PCA(n_components=2, random_state=RANDOM_SEED)
    coords = pca.fit_transform(X_scaled)

    features["cluster"] = labels
    features["pca_x"] = coords[:, 0]
    features["pca_y"] = coords[:, 1]

    # Assign human-readable labels based on avg_mastery
    cluster_stats = (
        features
        .groupby("cluster")
        .agg(
            avg_mastery=("avg_mastery", "mean"),
            avg_improvement=("avg_improvement", "mean"),
            size=("student_id", "count"),
        )
        .sort_values("avg_mastery", ascending=False)
    )

    # Map cluster IDs to labels (highest mastery → "High Performers")
    label_map = {}
    available_labels = CLUSTER_LABELS.copy()
    for cluster_id, row in cluster_stats.iterrows():
        if available_labels:
            label_map[int(cluster_id)] = available_labels.pop(0)
        else:
            label_map[int(cluster_id)] = f"Cluster {cluster_id}"

    features["cluster_label"] = features["cluster"].map(label_map)

    metrics = {
        "task": "clustering",
        "model": "KMeans",
        "purpose": "Student Clustering",
        "evaluation_type": "Development Evaluation",
        "synthetic_data": True,
        "n_students": int(len(features)),
        "n_clusters": int(n_clusters),
        "silhouette_score": sil,
        "pca_explained_variance": pca.explained_variance_ratio_.tolist(),
        "clusters": {
            label: {
                "size": int(row["size"]),
                "avg_mastery": float(row["avg_mastery"]),
                "avg_improvement": float(row["avg_improvement"]),
            }
            for cid, row in cluster_stats.iterrows()
            for label in [label_map[int(cid)]]
        },
    }

    if verbose:
        print("=" * 60)
        print("🎯 Student Clusterer — Built")
        print("=" * 60)
        print(f"   Students:            {metrics['n_students']}")
        print(f"   Clusters:            {metrics['n_clusters']}")
        print(f"   Silhouette score:    {metrics['silhouette_score']:.4f}")
        print(f"   PCA variance:        {metrics['pca_explained_variance']}")
        print()
        print("📋 Clusters:")
        for label, info in metrics["clusters"].items():
            print(
                f"   {label:22s} "
                f"size={info['size']:5d}  "
                f"avg_mastery={info['avg_mastery']:.1f}%  "
                f"avg_improv={info['avg_improvement']:.2f}"
            )

    return {
        "kmeans": kmeans,
        "scaler": scaler,
        "pca": pca,
        "labels": labels,
        "features": features,
        "feature_cols": feature_cols,
        "label_map": label_map,
        "metrics": metrics,
    }


def save_clusterer(trained):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "kmeans": trained["kmeans"],
        "scaler": trained["scaler"],
        "pca": trained["pca"],
        "feature_cols": trained["feature_cols"],
        "label_map": trained["label_map"],
    }
    joblib.dump(payload, CLUSTERER_MODEL_PATH)

    metrics_dir = MODELS_DIR / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    with open(metrics_dir / "clusterer_metrics.json", "w", encoding="utf-8") as f:
        json.dump(trained["metrics"], f, indent=2)

    print(f"\n✅ Clusterer saved: {CLUSTERER_MODEL_PATH}")
    print(f"✅ Metrics saved: {metrics_dir / 'clusterer_metrics.json'}")


def load_clusterer():
    if not CLUSTERER_MODEL_PATH.exists():
        return None
    return joblib.load(CLUSTERER_MODEL_PATH)


def predict_cluster(payload, features_dict):
    feature_cols = payload["feature_cols"]
    row = {col: float(features_dict.get(col, 0)) for col in feature_cols}
    import pandas as pd
    x = pd.DataFrame([row], columns=feature_cols)
    x_scaled = payload["scaler"].transform(x)
    cluster_id = int(payload["kmeans"].predict(x_scaled)[0])
    coords = payload["pca"].transform(x_scaled)[0]

    return {
        "cluster": cluster_id,
        "cluster_label": payload["label_map"].get(cluster_id, f"Cluster {cluster_id}"),
        "pca_x": float(coords[0]),
        "pca_y": float(coords[1]),
    }
