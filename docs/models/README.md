# ML Model Cards

Documentation for all 8 machine learning models in the Smart Knowledge Gap System.

---

## 📋 All Models

| # | Model | Algorithm | Task | Performance |
|---|-------|-----------|------|-------------|
| 1 | [Risk Predictor](risk_predictor.md) | Gradient Boosting | Binary classification | **F1 = 89.63%** |
| 2 | Performance Predictor | Random Forest | 4-class classification | Multi-class |
| 3 | Concept Recommender | Hybrid filtering | Ranking | — |
| 4 | [Student Clusterer](student_clusterer.md) | K-Means + PCA | Clustering | 4 clusters |
| 5 | [Knowledge Tracing](knowledge_tracing.md) | LSTM | Sequence prediction | **Acc = 70.83%** |
| 6 | SHAP Explainer | TreeExplainer | Feature attribution | — |
| 7 | LLM + RAG Assistant | Groq + Qdrant | Q&A | 675 docs |
| 8 | RL Agent (DQN) | Deep Q-Network | Adaptive selection | Reward = 18.77 |

---

## 🎯 Quick Links

- [Risk Predictor →](risk_predictor.md)
- [Knowledge Tracing →](knowledge_tracing.md)

---

## 🧠 Training All Models

```bash
python -m app.ml.train_all
```

---

**Last Updated:** 2026-09-20