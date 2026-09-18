"""
Centralized configuration for the ML layer.
"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Random seed for reproducibility
RANDOM_SEED = 42

# Synthetic data
SYNTHETIC_STUDENT_COUNT = 2000

# Model output paths
PERFORMANCE_MODEL_PATH = MODELS_DIR / "student_performance_model.joblib"
RECOMMENDER_MODEL_PATH = MODELS_DIR / "concept_recommender_model.joblib"
CLUSTERER_MODEL_PATH = MODELS_DIR / "student_clusterer_model.joblib"
OUTCOME_MODEL_PATH = MODELS_DIR / "learning_outcome_model.joblib"

# Metrics output paths
METRICS_DIR = MODELS_DIR / "metrics"

# Question types (matching the question bank)
QUESTION_TYPES = [
    "Understanding",
    "Application",
    "Reasoning",
    "Problem Solving",
    "Misconception Detection",
    "Transfer",
]

# Mastery thresholds
MASTERY_THRESHOLDS = {
    "Strong": 80.0,
    "Adequate": 60.0,
    "Weak": 40.0,
}
