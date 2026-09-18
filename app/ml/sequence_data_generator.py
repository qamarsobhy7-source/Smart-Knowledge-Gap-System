"""
Sequence Data Generator for Knowledge Tracing.

Generates synthetic sequences of student answers over time,
used to train the LSTM-based Knowledge Tracing model.

Each sequence represents ONE student's interaction history:
    [concept_1, correct_1, concept_2, correct_2, ...]
"""

import numpy as np
import pandas as pd

from .config import DATA_DIR, RANDOM_SEED


def _load_concepts():
    path = DATA_DIR / "concepts_final.csv"
    return pd.read_csv(path)


def generate_sequence_dataset(
    n_students=2000,
    min_length=20,
    max_length=80,
    n_concepts=45,
    seed=RANDOM_SEED,
):
    """
    Generate synthetic sequences for knowledge tracing.

    Returns a list of dicts:
        {
            "student_id": int,
            "concepts": [int, int, ...],       # concept IDs
            "correct": [0, 1, 0, ...],         # correctness per step
            "mastery_curve": [float, ...],     # true mastery at each step
        }
    """
    rng = np.random.default_rng(seed)

    concepts_df = _load_concepts()
    concept_ids = concepts_df["concept_id"].tolist()

    # Latent difficulty per concept
    concept_difficulty = {
        int(row["concept_id"]): {
            "Beginner": 0.15,
            "Intermediate": 0.30,
            "Advanced": 0.45,
        }[row["difficulty"]]
        for _, row in concepts_df.iterrows()
    }

    sequences = []

    for student_id in range(1, n_students + 1):
        # Student's initial ability
        initial_ability = float(rng.beta(2, 2))
        learning_rate = float(rng.beta(3, 3))

        # Per-concept latent mastery (starts lower, grows)
        concept_mastery = {
            cid: float(np.clip(initial_ability - concept_difficulty[cid] / 2, 0.05, 0.5))
            for cid in concept_ids
        }

        length = int(rng.integers(min_length, max_length + 1))

        # Per-concept personal skill (student-consistent)
        # This gives the LSTM a learnable signal: same concept → similar ability
        concept_skill = {
            cid: float(np.clip(initial_ability + rng.normal(0, 0.08), 0.0, 1.0))
            for cid in concept_ids
        }

        # Per-concept learning rate (some concepts are learned faster)
        concept_learning = {
            cid: float(np.clip(learning_rate + rng.normal(0, 0.05), 0.01, 0.5))
            for cid in concept_ids
        }

        # Track counts per concept (frequency matters)
        seen_counts = {cid: 0 for cid in concept_ids}

        seq_concepts = []
        seq_correct = []
        seq_mastery = []

        # Weighted concept sampling (student focuses on a subset)
        preferred = set(rng.choice(concept_ids, size=8, replace=False))

        for step in range(length):
            # 70% chance to pick from preferred concepts
            if rng.random() < 0.7:
                cid = int(rng.choice(list(preferred)))
            else:
                cid = int(rng.choice(concept_ids))

            # Current mastery depends on skill + practice effect
            practice_effect = 1.0 - np.exp(-seen_counts[cid] * concept_learning[cid])
            m = float(np.clip(
                concept_skill[cid] * (0.3 + 0.7 * practice_effect),
                0.0, 1.0
            ))

            # Add small noise (unpredictable factors)
            p_correct = float(np.clip(m + rng.normal(0, 0.05), 0.02, 0.98))
            correct = int(rng.random() < p_correct)

            seq_concepts.append(cid)
            seq_correct.append(correct)
            seq_mastery.append(m)
            seen_counts[cid] += 1

        sequences.append({
            "student_id": student_id,
            "concepts": seq_concepts,
            "correct": seq_correct,
            "mastery_curve": seq_mastery,
        })

    return sequences


def save_sequence_dataset(
    output_path=None,
    n_students=2000,
    seed=RANDOM_SEED,
):
    """Generate and save sequence dataset as JSON."""
    import json

    if output_path is None:
        output_path = DATA_DIR / "synthetic_knowledge_tracing_data.json"

    sequences = generate_sequence_dataset(
        n_students=n_students,
        seed=seed,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sequences, f)

    print(f"✅ Sequence dataset saved: {output_path}")
    print(f"   📊 {len(sequences)} sequences")
    print(f"   📏 avg length: {np.mean([len(s['correct']) for s in sequences]):.1f}")

    return sequences
