"""
Train All ML Models — One Command to Reproduce Everything.

This script trains all 8 ML models from scratch:
  1. Risk Predictor (Gradient Boosting)
  2. Performance Predictor (Random Forest)
  3. Concept Recommender (Hybrid)
  4. Student Clusterer (K-Means + PCA)
  5. Knowledge Tracing (LSTM)
  6. RL Agent (DQN)

Usage:
    python -m app.ml.train_all
or:
    from ml.train_all import train_and_save_all
    train_and_save_all()
"""

import json
import time
from pathlib import Path

from .config import DATA_DIR, MODELS_DIR


def _log(msg):
    print(msg, flush=True)


def train_and_save_all(verbose=True):
    """Train all ML models from scratch and save them to disk."""
    start_time = time.time()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    (MODELS_DIR / "metrics").mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # 1. Generate synthetic data
    # ------------------------------------------------------------
    _log("=" * 60)
    _log("STEP 1/6 — Generating synthetic data")
    _log("=" * 60)

    from .data_generator import save_synthetic_dataset
    from .sequence_data_generator import save_sequence_dataset

    df = save_synthetic_dataset()
    sequences = save_sequence_dataset()

    # ------------------------------------------------------------
    # 2. Risk Predictor
    # ------------------------------------------------------------
    _log("")
    _log("=" * 60)
    _log("STEP 2/6 — Training Risk Predictor")
    _log("=" * 60)

    from .risk_predictor import (
        train_risk_predictor,
        save_risk_predictor,
    )

    trained = train_risk_predictor(df)
    save_risk_predictor(trained)

    # ------------------------------------------------------------
    # 3. Performance Predictor
    # ------------------------------------------------------------
    _log("")
    _log("=" * 60)
    _log("STEP 3/6 — Training Performance Predictor")
    _log("=" * 60)

    from .performance_predictor import (
        train_performance_predictor,
        save_performance_predictor,
    )

    trained = train_performance_predictor(df)
    save_performance_predictor(trained)

    # ------------------------------------------------------------
    # 4. Concept Recommender
    # ------------------------------------------------------------
    _log("")
    _log("=" * 60)
    _log("STEP 4/6 — Training Concept Recommender")
    _log("=" * 60)

    from .concept_recommender import (
        train_recommender,
        save_recommender,
    )

    import pandas as pd
    concepts_df = pd.read_csv(DATA_DIR / "concepts_final.csv")
    question_bank_df = pd.read_csv(DATA_DIR / "final_question_bank_270.csv")

    payload = train_recommender(df, concepts_df, question_bank_df)
    save_recommender(payload)

    # ------------------------------------------------------------
    # 5. Student Clusterer
    # ------------------------------------------------------------
    _log("")
    _log("=" * 60)
    _log("STEP 5/6 — Training Student Clusterer")
    _log("=" * 60)

    from .student_clusterer import (
        train_clusterer,
        save_clusterer,
    )

    trained = train_clusterer(df, n_clusters=4)
    save_clusterer(trained)

    # ------------------------------------------------------------
    # 6. Knowledge Tracing + RL + RAG
    # ------------------------------------------------------------
    _log("")
    _log("=" * 60)
    _log("STEP 6/6 — Training KT (LSTM), RL (DQN), and building RAG")
    _log("=" * 60)

    # Knowledge Tracing
    _log("")
    _log("  - Knowledge Tracing (LSTM)...")
    from .knowledge_tracing import (
        KnowledgeTracingModel,
        save_knowledge_tracing,
    )

    kt_model = KnowledgeTracingModel(n_concepts=45)
    kt_model.fit(sequences, epochs=15, verbose=False)
    save_knowledge_tracing(kt_model)

    # RL Agent
    _log("")
    _log("  - RL Agent (DQN)...")
    import numpy as np
    from .rl_environment import LearningEnvironment
    from .rl_dqn_agent import train_dqn, save_dqn_agent

    difficulty_map = {"Beginner": 0.2, "Intermediate": 0.5, "Advanced": 0.8}
    concepts_df_sorted = concepts_df.sort_values("concept_id").reset_index(drop=True)
    difficulty_arr = concepts_df_sorted["difficulty"].map(difficulty_map).values.astype(np.float32)

    env = LearningEnvironment(n_concepts=45, max_steps=30, seed=42)
    env.set_difficulty(difficulty_arr)
    agent, metrics = train_dqn(env, n_episodes=1000, verbose=False)
    save_dqn_agent(agent, metrics)

    # RAG
    _log("")
    _log("  - Building RAG vector store...")
    from .rag_engine import build_vector_store
    build_vector_store(verbose=False)
    _log("    ✅ RAG vector store built")

    # ------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------
    elapsed = time.time() - start_time
    _log("")
    _log("=" * 60)
    _log(f"🎉 ALL MODELS TRAINED in {elapsed/60:.1f} minutes")
    _log("=" * 60)
    _log("")
    _log("📋 Trained models:")
    for f in sorted(MODELS_DIR.glob("*.joblib")):
        _log(f"   ✅ {f.name} ({f.stat().st_size / 1024:.0f} KB)")
    for f in sorted(MODELS_DIR.glob("*.pt")):
        _log(f"   ✅ {f.name} ({f.stat().st_size / 1024:.0f} KB)")

    return True


if __name__ == "__main__":
    train_and_save_all()
