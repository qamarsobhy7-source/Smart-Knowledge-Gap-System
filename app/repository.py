
import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


QUESTION_BANK_PATH = DATA_DIR / "final_question_bank_270.csv"
CONCEPTS_PATH = DATA_DIR / "concepts_final.csv"
LEARNING_CONTENT_PATH = DATA_DIR / "learning_content_FINAL.csv"
PRACTICE_PATH = DATA_DIR / "practice_questions_FINAL.csv"


def load_question_bank():
    if not QUESTION_BANK_PATH.is_file():
        raise FileNotFoundError(
            "Question Bank file was not found."
        )

    return pd.read_csv(QUESTION_BANK_PATH)


def load_concepts():
    if not CONCEPTS_PATH.is_file():
        raise FileNotFoundError(
            "Concept Master file was not found."
        )

    return pd.read_csv(CONCEPTS_PATH)


def load_learning_content():
    if not LEARNING_CONTENT_PATH.is_file():
        raise FileNotFoundError(
            "Learning Content file was not found."
        )

    return pd.read_csv(LEARNING_CONTENT_PATH)


def load_practice_questions():
    if not PRACTICE_PATH.is_file():
        raise FileNotFoundError(
            "Practice Questions file was not found."
        )

    return pd.read_csv(PRACTICE_PATH)


def get_concept(concept_id):
    concepts = load_concepts()

    matches = concepts[
        concepts["concept_id"] == int(concept_id)
    ]

    if matches.empty:
        return None

    return matches.iloc[0].to_dict()


def get_questions_for_concept(concept_id):
    questions = load_question_bank()

    result = questions[
        questions["concept_id"] == int(concept_id)
    ].copy()

    return result


def get_practice_for_concept(concept_id):
    practice = load_practice_questions()

    result = practice[
        practice["concept_id"] == int(concept_id)
    ].copy()

    return result


def get_learning_content_for_concept(concept_id):
    content = load_learning_content()

    matches = content[
        content["concept_id"] == int(concept_id)
    ]

    if matches.empty:
        return None

    return matches.iloc[0].to_dict()


def get_all_concepts():
    return load_concepts().copy()
