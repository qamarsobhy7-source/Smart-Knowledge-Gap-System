
import pandas as pd


GAP_SEVERITY_SCORES = {
    "Critical": 1.00,
    "Weak": 0.75,
    "Adequate": 0.25,
    "Strong": 0.00
}


PRIORITY_THRESHOLDS = {
    "High": 0.80,
    "Medium": 0.60
}


GAP_WEIGHT = 0.70
DEPENDENCY_WEIGHT = 0.30
BLOCKING_BONUS = 0.10


def calculate_dependency_counts(concepts_df):
    required_columns = {
        "concept_id",
        "prerequisites"
    }

    missing = (
        required_columns
        - set(concepts_df.columns)
    )

    if missing:
        raise ValueError(
            f"Missing concept columns: {sorted(missing)}"
        )

    dependency_counts = {
        int(concept_id): 0
        for concept_id
        in concepts_df["concept_id"]
    }

    for _, row in concepts_df.iterrows():

        prerequisites = row["prerequisites"]

        if pd.isna(prerequisites):
            continue

        prerequisites = str(
            prerequisites
        ).strip()

        if not prerequisites:
            continue

        for prerequisite in (
            prerequisites
            .replace(";", ",")
            .split(",")
        ):

            prerequisite = (
                prerequisite.strip()
            )

            if prerequisite:
                prerequisite_id = int(
                    prerequisite
                )

                if prerequisite_id not in dependency_counts:
                    raise ValueError(
                        "Unknown prerequisite concept: "
                        f"{prerequisite_id}"
                    )

                dependency_counts[
                    prerequisite_id
                ] += 1

    return dependency_counts


def calculate_student_priority(
    diagnosis_df,
    concepts_df
):

    required_diagnosis_columns = {
        "concept_id",
        "mastery",
        "gap_level",
        "gap_score"
    }

    missing = (
        required_diagnosis_columns
        - set(diagnosis_df.columns)
    )

    if missing:
        raise ValueError(
            "Missing diagnosis columns: "
            f"{sorted(missing)}"
        )

    if "concept_id" not in concepts_df.columns:
        raise ValueError(
            "Concept Master must contain concept_id."
        )

    dependency_counts = (
        calculate_dependency_counts(
            concepts_df
        )
    )

    max_dependency = max(
        dependency_counts.values(),
        default=0
    )

    result = diagnosis_df.copy()

    result["dependency_count"] = (
        result["concept_id"]
        .map(dependency_counts)
        .fillna(0)
        .astype(int)
    )

    if max_dependency > 0:
        result["dependency_impact"] = (
            result["dependency_count"]
            / max_dependency
        )
    else:
        result["dependency_impact"] = 0.0

    result["gap_severity"] = (
        result["gap_level"]
        .map(GAP_SEVERITY_SCORES)
    )

    if result["gap_severity"].isna().any():
        invalid_levels = sorted(
            result.loc[
                result["gap_severity"].isna(),
                "gap_level"
            ].astype(str).unique()
        )

        raise ValueError(
            "Invalid gap levels: "
            f"{invalid_levels}"
        )

    result["blocked_by_prerequisite"] = False

    concept_mastery = dict(
        zip(
            result["concept_id"].astype(int),
            result["mastery"].astype(float)
        )
    )

    prerequisite_map = {}

    for _, row in concepts_df.iterrows():

        concept_id = int(
            row["concept_id"]
        )

        prerequisites = row["prerequisites"]

        if pd.isna(prerequisites):
            prerequisite_map[concept_id] = []
            continue

        prerequisites = str(
            prerequisites
        ).strip()

        if not prerequisites:
            prerequisite_map[concept_id] = []
            continue

        prerequisite_map[concept_id] = [
            int(p.strip())
            for p in prerequisites
            .replace(";", ",")
            .split(",")
            if p.strip()
        ]

    for concept_id in result["concept_id"].astype(int):

        prerequisite_ids = prerequisite_map.get(
            concept_id,
            []
        )

        blocked = any(
            concept_mastery.get(
                prerequisite_id,
                100.0
            ) < 60.0
            for prerequisite_id
            in prerequisite_ids
        )

        result.loc[
            result["concept_id"] == concept_id,
            "blocked_by_prerequisite"
        ] = blocked

    result["base_priority"] = (
        result["gap_severity"]
        * GAP_WEIGHT
        +
        result["dependency_impact"]
        * DEPENDENCY_WEIGHT
    )

    result["blocking_bonus"] = (
        result["blocked_by_prerequisite"]
        .astype(float)
        * BLOCKING_BONUS
    )

    result["priority_score"] = (
        result["base_priority"]
        + result["blocking_bonus"]
    ).clip(
        upper=1.0
    )

    def classify_priority(score):

        score = float(score)

        if score >= PRIORITY_THRESHOLDS["High"]:
            return "High"

        if score >= PRIORITY_THRESHOLDS["Medium"]:
            return "Medium"

        return "Low"

    result["priority_level"] = (
        result["priority_score"]
        .apply(classify_priority)
    )

    result = result.sort_values(
        by=[
            "priority_score",
            "concept_id"
        ],
        ascending=[
            False,
            True
        ]
    ).reset_index(drop=True)

    result["priority_rank"] = (
        range(1, len(result) + 1)
    )

    return result
