"""
Knowledge Tracing Model — LSTM-based.

Predicts the probability that a student will answer the next question
correctly, given their full interaction history.

Architecture:
    - Input: (concept_id, correctness) pairs
    - Embedding layer for concepts
    - LSTM over the sequence
    - Output: probability of correct answer for the next concept

Reference:
    Piech et al. (2015) — "Deep Knowledge Tracing"
"""

import json

import joblib
import numpy as np

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    nn = None
    DataLoader = None
    TensorDataset = None
    TORCH_AVAILABLE = False

from .config import MODELS_DIR, RANDOM_SEED


KT_MODEL_PATH = MODELS_DIR / "knowledge_tracing_model.joblib"
KT_TORCH_PATH = MODELS_DIR / "knowledge_tracing_model.pt"
KT_METRICS_PATH = MODELS_DIR / "metrics" / "knowledge_tracing_metrics.json"


def _build_vocabulary(sequences):
    """Map concept IDs to dense indices."""
    concept_ids = set()
    for seq in sequences:
        concept_ids.update(seq["concepts"])
    sorted_ids = sorted(concept_ids)
    concept_to_idx = {cid: i + 1 for i, cid in enumerate(sorted_ids)}  # 0 = padding
    idx_to_concept = {i: cid for cid, i in concept_to_idx.items()}
    return concept_to_idx, idx_to_concept


def _encode_sequences(sequences, concept_to_idx, max_length=80):
    """
    Encode sequences into (concept_seq, correct_seq) tensors.
    """
    import torch

    n = len(sequences)
    concept_tensor = np.zeros((n, max_length), dtype=np.int64)
    correct_tensor = np.zeros((n, max_length), dtype=np.float32)
    length_tensor = np.zeros(n, dtype=np.int64)
    target_tensor = np.zeros((n, max_length), dtype=np.float32)

    for i, seq in enumerate(sequences):
        concepts = seq["concepts"][:max_length]
        correct = seq["correct"][:max_length]
        L = len(concepts)

        for j in range(L):
            concept_tensor[i, j] = concept_to_idx.get(concepts[j], 0)
            correct_tensor[i, j] = correct[j]

        # Target: predict next-step correctness (shift by 1)
        for j in range(1, L):
            target_tensor[i, j - 1] = correct[j]

        length_tensor[i] = L

    return (
        torch.from_numpy(concept_tensor),
        torch.from_numpy(correct_tensor),
        torch.from_numpy(length_tensor),
        torch.from_numpy(target_tensor),
    )


class KnowledgeTracingModel:
    """LSTM-based knowledge tracing model."""

    def __init__(self, n_concepts, embed_dim=32, hidden_dim=64, dropout=0.2):
        import torch
        import torch.nn as nn

        class _KT(nn.Module):
            def __init__(self):
                super().__init__()
                self.concept_embed = nn.Embedding(
                    n_concepts + 1, embed_dim, padding_idx=0
                )
                self.correct_embed = nn.Embedding(2, embed_dim)
                self.lstm = nn.LSTM(
                    input_size=embed_dim * 2,
                    hidden_size=hidden_dim,
                    num_layers=1,
                    batch_first=True,
                    dropout=0.0,
                )
                self.dropout = nn.Dropout(dropout)
                self.output = nn.Linear(hidden_dim, 1)

            def forward(self, concepts, correct):
                c_emb = self.concept_embed(concepts)
                r_emb = self.correct_embed(correct.long())
                x = torch.cat([c_emb, r_emb], dim=-1)
                out, _ = self.lstm(x)
                out = self.dropout(out)
                logits = self.output(out).squeeze(-1)
                return logits

        self.n_concepts = n_concepts
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self._model = _KT()

    @property
    def model(self):
        return self._model

    def fit(
        self,
        sequences,
        epochs=8,
        batch_size=64,
        lr=1e-3,
        verbose=True,
    ):
        """Train the model."""
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset

        torch.manual_seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)

        concept_to_idx, idx_to_concept = _build_vocabulary(sequences)

        # Split train/val
        n = len(sequences)
        idx = np.random.permutation(n)
        n_train = int(n * 0.8)
        train_seqs = [sequences[i] for i in idx[:n_train]]
        val_seqs = [sequences[i] for i in idx[n_train:]]

        train_tensors = _encode_sequences(train_seqs, concept_to_idx)
        val_tensors = _encode_sequences(val_seqs, concept_to_idx)

        train_ds = TensorDataset(*train_tensors)
        train_loader = DataLoader(
            train_ds, batch_size=batch_size, shuffle=True
        )

        optimizer = torch.optim.Adam(self._model.parameters(), lr=lr)
        criterion = nn.BCEWithLogitsLoss(reduction="none")

        history = []
        for epoch in range(epochs):
            self._model.train()
            total_loss = 0.0
            total_count = 0

            for c, r, L, y in train_loader:
                optimizer.zero_grad()
                logits = self._model(c, r)
                loss = criterion(logits, y)

                # Mask padding
                mask = torch.zeros_like(y)
                for i in range(y.size(0)):
                    mask[i, : max(L[i].item() - 1, 0)] = 1.0
                loss = (loss * mask).sum() / mask.sum().clamp(min=1.0)

                loss.backward()
                optimizer.step()

                total_loss += loss.item() * mask.sum().item()
                total_count += mask.sum().item()

            avg_loss = total_loss / max(total_count, 1)
            history.append(avg_loss)

            if verbose:
                print(f"   Epoch {epoch + 1}/{epochs} — loss: {avg_loss:.4f}")

        # Evaluate on validation
        metrics = self._evaluate(val_tensors)
        metrics["n_train"] = len(train_seqs)
        metrics["n_val"] = len(val_seqs)
        metrics["history"] = history

        if verbose:
            print("=" * 60)
            print("📊 Knowledge Tracing — Metrics")
            print("=" * 60)
            print(f"   Val accuracy:  {metrics['accuracy']:.4f}")
            print(f"   Val AUC:       {metrics['auc']:.4f}")
            print(f"   Val loss:      {metrics['loss']:.4f}")

        self.concept_to_idx = concept_to_idx
        self.idx_to_concept = idx_to_concept
        self.metrics = metrics

        return metrics

    def _evaluate(self, tensors):
        import torch
        import torch.nn as nn
        from sklearn.metrics import roc_auc_score, accuracy_score

        c, r, L, y = tensors

        self._model.eval()
        with torch.no_grad():
            logits = self._model(c, r)
            probs = torch.sigmoid(logits)

        # Build mask
        mask = torch.zeros_like(y)
        for i in range(y.size(0)):
            mask[i, : max(L[i].item() - 1, 0)] = 1.0

        probs_np = probs.numpy()
        y_np = y.numpy()
        mask_np = mask.numpy()

        valid = mask_np == 1.0
        probs_flat = probs_np[valid]
        y_flat = y_np[valid]

        loss = float(
            -np.mean(
                y_flat * np.log(probs_flat + 1e-7)
                + (1 - y_flat) * np.log(1 - probs_flat + 1e-7)
            )
        )

        preds = (probs_flat > 0.5).astype(int)

        return {
            "task": "knowledge_tracing",
            "model": "LSTM",
            "purpose": "Knowledge Tracing (next-step correctness)",
            "evaluation_type": "Development Evaluation",
            "synthetic_data": True,
            "accuracy": float(accuracy_score(y_flat, preds)),
            "auc": float(roc_auc_score(y_flat, probs_flat)),
            "loss": loss,
        }


def train_knowledge_tracing(sequences, verbose=True):
    """Build, train, and return a KnowledgeTracingModel."""
    n_concepts = 45
    model = KnowledgeTracingModel(n_concepts=n_concepts)
    model.fit(sequences, verbose=verbose)
    return model


def save_knowledge_tracing(model):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Save PyTorch state dict
    import torch
    torch.save(model.model.state_dict(), KT_TORCH_PATH)

    # Save metadata via joblib
    joblib.dump(
        {
            "n_concepts": model.n_concepts,
            "embed_dim": model.embed_dim,
            "hidden_dim": model.hidden_dim,
            "concept_to_idx": model.concept_to_idx,
            "idx_to_concept": model.idx_to_concept,
        },
        KT_MODEL_PATH,
    )

    # Save metrics
    KT_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KT_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(model.metrics, f, indent=2)

    print(f"\n✅ KT model saved: {KT_TORCH_PATH}")
    print(f"✅ KT metadata: {KT_MODEL_PATH}")
    print(f"✅ KT metrics: {KT_METRICS_PATH}")


def load_knowledge_tracing():
    if not (KT_TORCH_PATH.exists() and KT_MODEL_PATH.exists()):
        return None

    import torch
    metadata = joblib.load(KT_MODEL_PATH)
    model = KnowledgeTracingModel(
        n_concepts=metadata["n_concepts"],
        embed_dim=metadata["embed_dim"],
        hidden_dim=metadata["hidden_dim"],
    )
    model.model.load_state_dict(torch.load(KT_TORCH_PATH))
    model.model.eval()
    model.concept_to_idx = metadata["concept_to_idx"]
    model.idx_to_concept = metadata["idx_to_concept"]
    return model


def predict_next_correctness(kt_model, concepts, correct):
    """
    Predict probability of correct answer on the NEXT concept.

    Args:
        kt_model: KnowledgeTracingModel instance
        concepts: list of concept IDs (history)
        correct: list of correctness (history)

    Returns:
        probability (0-1)
    """
    import torch

    concept_idx = [kt_model.concept_to_idx.get(c, 0) for c in concepts]
    concept_tensor = torch.tensor([concept_idx], dtype=torch.long)
    correct_tensor = torch.tensor([correct], dtype=torch.float32)

    with torch.no_grad():
        logits = kt_model.model(concept_tensor, correct_tensor)
        prob = torch.sigmoid(logits[0, -1]).item()

    return prob
