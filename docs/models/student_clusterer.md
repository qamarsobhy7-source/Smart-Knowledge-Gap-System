# Model Card: Student Clusterer

## Model Details

| Field | Value |
|-------|-------|
| **Model Name** | Student Clusterer |
| **Version** | 1.0.1 |
| **Type** | Unsupervised Clustering |
| **Algorithm** | K-Means + PCA |
| **Framework** | scikit-learn |
| **File** | `models/student_clusterer.joblib` |

## Intended Use

Segment students into archetypes based on learning behavior, so interventions can be **personalized per group**.

## The 4 Clusters

| Cluster | Name | Description |
|---------|------|-------------|
| **0** | 🌱 Beginners | Low scores, high struggle, need foundational support |
| **1** | 🔍 Explorers | Moderate scores, high engagement, exploring topics |
| **2** | 🎯 Achievers | High scores, consistent effort, need challenges |
| **3** | 🏆 Experts | Very high scores, fast learners, ready for advanced content |

## Features Used

- Average score
- Concepts mastered
- Time spent per concept
- Number of attempts per question
- Improvement trajectory
- Engagement frequency

## Dimensionality Reduction

- **Method:** PCA (Principal Component Analysis)
- **Components:** 2 (for visualization)
- **Variance Retained:** ~85%

## Training Data

- **Source:** Synthetic student profiles
- **Samples:** ~1,000
- **Features:** 6 behavioral dimensions

## Ethical Considerations

- ⚠️ Labels are **descriptive, not prescriptive** — a student in 'Beginners' isn't doomed
- ✅ Designed to **support** students, not label them permanently
- ✅ Cluster membership can change over time

## Limitations

- Cluster boundaries can be fuzzy
- New students may be misclassified with little data
- Clusters derived from synthetic data

---

**Last Updated:** 2026-09-20