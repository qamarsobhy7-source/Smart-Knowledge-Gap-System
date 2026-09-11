
import pandas as pd


LEARNING_TARGET_LEVELS = {
    "Weak",
    "Critical"
}


def build_prerequisite_map(concepts_df):

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
            "Missing concept columns: "
            f"{sorted(missing)}"
        )

    prerequisite_map = {}

    valid_concepts = set(
        concepts_df["concept_id"]
        .astype(int)
    )

    for _, row in concepts_df.iterrows():

        concept_id = int(
            row["concept_id"]
        )

        value = row["prerequisites"]

        if pd.isna(value):
            prerequisite_map[concept_id] = []
            continue

        value = str(value).strip()

        if not value:
            prerequisite_map[concept_id] = []
            continue

        prerequisites = [
            int(part.strip())
            for part in value
            .replace(";", ",")
            .split(",")
            if part.strip()
        ]

        unknown = [
            prerequisite
            for prerequisite in prerequisites
            if prerequisite not in valid_concepts
        ]

        if unknown:
            raise ValueError(
                f"Unknown prerequisites for concept "
                f"{concept_id}: {unknown}"
            )

        if concept_id in prerequisites:
            raise ValueError(
                f"Concept {concept_id} "
                "cannot depend on itself."
            )

        prerequisite_map[concept_id] = prerequisites

    return prerequisite_map


def build_personalized_learning_path(
    diagnosis_df,
    priority_df,
    concepts_df
):

    required_diagnosis = {
        "concept_id",
        "mastery",
        "gap_level"
    }

    required_priority = {
        "concept_id",
        "priority_score",
        "priority_level"
    }

    missing_diagnosis = (
        required_diagnosis
        - set(diagnosis_df.columns)
    )

    if missing_diagnosis:
        raise ValueError(
            "Missing diagnosis columns: "
            f"{sorted(missing_diagnosis)}"
        )

    missing_priority = (
        required_priority
        - set(priority_df.columns)
    )

    if missing_priority:
        raise ValueError(
            "Missing priority columns: "
            f"{sorted(missing_priority)}"
        )

    prerequisite_map = (
        build_prerequisite_map(
            concepts_df
        )
    )

    concept_info = (
        concepts_df
        .set_index("concept_id")
        .to_dict("index")
    )

    diagnosis = diagnosis_df.copy()
    priority = priority_df.copy()

    diagnosis["concept_id"] = (
        diagnosis["concept_id"]
        .astype(int)
    )

    priority["concept_id"] = (
        priority["concept_id"]
        .astype(int)
    )

    merged = diagnosis.merge(
        priority[
            [
                "concept_id",
                "priority_score",
                "priority_level"
            ]
        ],
        on="concept_id",
        how="inner",
        validate="one_to_one"
    )

    if len(merged) != len(diagnosis):
        raise ValueError(
            "Diagnosis and priority concepts "
            "do not match."
        )

    target_concepts = set(
        merged.loc[
            merged["gap_level"].isin(
                LEARNING_TARGET_LEVELS
            ),
            "concept_id"
        ]
        .astype(int)
    )

    selected = []
    remaining = set(target_concepts)

    completed = set()

    while remaining:

        available = []

        for concept_id in remaining:

            prerequisites = (
                prerequisite_map.get(
                    concept_id,
                    []
                )
            )

            prerequisites_ready = all(
                prerequisite in completed
                or prerequisite not in target_concepts
                for prerequisite
                in prerequisites
            )

            if prerequisites_ready:
                available.append(
                    concept_id
                )

        if not available:
            raise ValueError(
                "Unable to build a valid "
                "prerequisite-aware learning path."
            )

        available_df = merged[
            merged["concept_id"].isin(
                available
            )
        ].copy()

        available_df = (
            available_df
            .sort_values(
                by=[
                    "priority_score",
                    "concept_id"
                ],
                ascending=[
                    False,
                    True
                ]
            )
        )

        selected_concept = int(
            available_df.iloc[0]["concept_id"]
        )

        selected.append(
            selected_concept
        )

        completed.add(
            selected_concept
        )

        remaining.remove(
            selected_concept
        )

    path_rows = []

    for step, concept_id in enumerate(
        selected,
        start=1
    ):

        row = merged.loc[
            merged["concept_id"] == concept_id
        ].iloc[0]

        info = concept_info[
            concept_id
        ]

        path_rows.append({
            "learning_step": step,
            "concept_id": concept_id,
            "concept_name": info[
                "concept_name"
            ],
            "subject_id": info[
                "subject_id"
            ],
            "difficulty": info[
                "difficulty"
            ],
            "mastery": float(
                row["mastery"]
            ),
            "gap_level": row[
                "gap_level"
            ],
            "priority_score": float(
                row["priority_score"]
            ),
            "priority_level": row[
                "priority_level"
            ]
        })

    return pd.DataFrame(
        path_rows
    )
