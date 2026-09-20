# Model Card: Knowledge Tracing

## Model Details

| Field | Value |
|-------|-------|
| **Model Name** | Knowledge Tracing LSTM |
| **Version** | 1.0.1 |
| **Type** | Sequence Prediction |
| **Algorithm** | Long Short-Term Memory (LSTM) |
| **Framework** | PyTorch |
| **Files** | `models/knowledge_tracing_model.pt`, `models/knowledge_tracing_model.joblib` |

## Intended Use

### Primary Use
Predict a student's probability of correctly answering a **next question** based on their historical answer sequence (knowledge tracing).

### Intended Users
- Adaptive assessment engine (question selection)
- Recommendation system
- Learning path generator

## Performance

| Metric | Value |
|--------|-------|
| **Accuracy** | **70.83%** |
| **Sequence Length** | 20 answers |
| **Embedding Dim** | 64 |
| **Hidden Dim** | 128 |

## Architecture

```
Input (sequence of answers)
    ↓
Embedding (64-d)
    ↓
LSTM (128 hidden units)
    ↓
Dense → Sigmoid
    ↓
P(correct next answer)
```

## Training Data

- **Source:** Generated answer sequences from simulated students
- **Samples:** ~10,000 sequences
- **Sequence length:** 20 answers per sample

## Ethical Considerations

- ✅ Predictions used **only** to improve learning experience
- ✅ No negative consequences for students
- ✅ Model is one of many inputs — not the only decision factor

## Limitations

- Cold-start problem: needs ≥5 answers for reliable prediction
- Trained on synthetic sequences
- Subject-specific (currently tuned for Computer Science)

---

**Last Updated:** 2026-09-20