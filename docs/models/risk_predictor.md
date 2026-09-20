# Model Card: Risk Predictor

## Model Details

| Field | Value |
|-------|-------|
| **Model Name** | Risk Predictor |
| **Version** | 1.0.1 |
| **Type** | Binary Classification |
| **Algorithm** | Gradient Boosting Classifier |
| **Framework** | scikit-learn |
| **File** | `models/student_risk_model.joblib` |

## Intended Use

### Primary Use
Predict whether a student is **at risk** of failing or dropping out, based on their assessment history and engagement patterns.

### Intended Users
- Teachers (early intervention)
- Students (self-awareness)
- Administrators (cohort analysis)

### Out-of-Scope Use
- Final grading decisions
- Disciplinary actions
- Any use not related to learning support

## Performance

| Metric | Value |
|--------|-------|
| **F1 Score** | **89.63%** |
| **Accuracy** | ~90% |
| **Precision** | ~89% |
| **Recall** | ~90% |

## Features

| Feature | Type | Description |
|---------|------|-------------|
| `avg_score` | float | Average assessment score (0-1) |
| `total_attempts` | int | Total questions attempted |
| `concepts_mastered` | int | Number of fully mastered concepts |
| `concepts_struggling` | int | Number of weak concepts |
| `days_since_last_session` | int | Days since last activity |
| `improvement_rate` | float | Score change over time |

## Training Data

- **Source:** Synthetic student data generator
- **Samples:** ~5,000 student profiles
- **Class Balance:** ~70% safe / 30% at-risk
- **Split:** 80% train / 20% test

## Ethical Considerations

- ⚠️ Model predictions are **advisory only** — not final decisions
- ⚠️ Should **never** be used punitively
- ✅ Supports **early intervention** and student success
- ✅ Predictions are **explainable** via SHAP

## Limitations

- Trained on synthetic data — may not reflect real student populations
- Requires ≥3 assessment sessions for reliable predictions
- Performance may vary across subjects

---

**Last Updated:** 2026-09-20