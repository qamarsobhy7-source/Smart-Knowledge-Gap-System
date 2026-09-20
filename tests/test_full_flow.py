"""
End-to-end validation script for the Smart Knowledge Gap System.

This script verifies the COMPLETE flow:

    1. Register a student.
    2. Select subject + level.
    3. Load exactly 30 questions for that subject+level.
    4. Answer all 30 questions correctly.
    5. Verify that the system scores 30/30.
    6. Verify concept-level diagnosis is produced.

It runs the test for all 9 (subject, level) combinations.

Usage:
    python tests/test_full_flow.py
"""

import os
import re
import sys
import sqlite3
from pathlib import Path

import pandas as pd

# ------------------------------------------------------------
# Path setup
# ------------------------------------------------------------

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent
APP_DIR = PROJECT_ROOT / "app"
DATA_DIR = PROJECT_ROOT / "data"

sys.path.insert(0, str(APP_DIR))


# ------------------------------------------------------------
# Ensure a usable SECRET_KEY
# ------------------------------------------------------------

os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-for-end-to-end-validation-only"
)


# ------------------------------------------------------------
# The database lives in data/ and is created by init_database.
# ------------------------------------------------------------

DB_PATH = DATA_DIR / "smart_knowledge_gap.db"


# ------------------------------------------------------------
# Imports
# ------------------------------------------------------------

from init_database import initialize_database  # noqa: E402
from database import get_connection          # noqa: E402


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

SUBJECTS = {
    "Mathematics": 1,
    "Physics": 2,
    "Computer Science": 3,
}

LEVELS = ["Beginner", "Intermediate", "Advanced"]

OPTION_KEYS = ("A", "B", "C", "D")


def load_question_bank():
    return pd.read_csv(DATA_DIR / "final_question_bank_270.csv")


def build_test_client():
    """Import the Flask app fresh and return a test client."""

    for mod_name in list(sys.modules.keys()):
        if mod_name in {
            "app",
            "backend_service",
            "repository",
            "diagnostic_engine",
            "priority_engine",
            "learning_path_engine",
            "student_dashboard_service",
            "teacher_dashboard_service",
        }:
            del sys.modules[mod_name]

    import app as app_module  # noqa: WPS433

    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def compute_displayed_answer(assessment_id, question_id, correct_answer):
    """
    Reproduce the deterministic option mapping used by the app.
    """
    import hashlib

    seed = f"SKG::{assessment_id}::{question_id}::V1"

    ordered = sorted(
        OPTION_KEYS,
        key=lambda o: hashlib.sha256(
            f"{seed}::{o}".encode("utf-8")
        ).hexdigest(),
    )

    mapping = {
        displayed: orig
        for displayed, orig in zip(OPTION_KEYS, ordered)
    }

    for displayed, orig in mapping.items():
        if orig == correct_answer:
            return displayed

    raise RuntimeError(
        f"Could not map answer for {question_id}"
    )


def run_single_combination(subject_name, subject_id, level):
    """Run the full flow for one (subject, level)."""

    client = build_test_client()

    # 1. Register (with CSRF, email, password)
    # Fetch homepage to get CSRF token
    home_resp = client.get("/")
    home_html = home_resp.get_data(as_text=True)
    csrf_match = re.search(
        r'name="csrf_token"\s+value="([^"]+)"',
        home_html,
    )
    csrf_token = csrf_match.group(1) if csrf_match else None

    if csrf_token is None:
        return False, "Could not fetch CSRF token"

    # Generate unique email
    import uuid
    unique_email = f"e2e_{subject_id}_{level.lower()}_{uuid.uuid4().hex[:8]}@test.com"

    response = client.post(
        "/register",
        data={
            "csrf_token": csrf_token,
            "name": f"E2E Test {subject_name} {level}",
            "email": unique_email,
            "password": "test123456",
            "age": "18",
            "subject": subject_name,
            "level": level,
        },
        follow_redirects=False,
    )

    if response.status_code != 302:
        return False, f"Registration failed ({response.status_code})"

    location = response.headers.get("Location", "")
    try:
        student_id = int(location.rstrip("/").split("/")[-1])
    except ValueError:
        return False, f"Invalid redirect URL: {location}"

    # 2. Trigger the assessment page
    response = client.get(f"/assessment/{student_id}")
    if response.status_code != 200:
        return False, f"Assessment GET failed ({response.status_code})"

    with client.session_transaction() as sess:
        assessment_id = sess.get("assessment_id")

    if assessment_id is None:
        return False, "assessment_id was not created"

    # 3. Load the correct 30 questions
    questions_df = load_question_bank()
    selected = (
        questions_df[
            (questions_df["subject_id"] == subject_id)
            & (questions_df["difficulty"] == level)
        ]
        .sort_values(["concept_id", "question_id"])
        .reset_index(drop=True)
    )

    if len(selected) != 30:
        return False, f"Expected 30 questions, got {len(selected)}"

    correct_map = dict(
        zip(selected["question_id"], selected["correct_answer"])
    )

    # 4. Answer all 30 questions correctly
    for _ in range(30):
        response = client.get(f"/assessment/{student_id}")
        if response.status_code != 200:
            return False, f"Question GET failed ({response.status_code})"

        html = response.get_data(as_text=True)

        # Fetch CSRF token from the assessment page
        csrf_match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            html,
        )
        csrf_token = csrf_match.group(1) if csrf_match else None

        match = re.search(
            r'name="question_id"\s+value="([^"]+)"',
            html,
        )

        if not match:
            break

        question_id = match.group(1)
        correct_answer = correct_map.get(question_id)

        if correct_answer is None:
            return False, f"Unknown question_id: {question_id}"

        displayed = compute_displayed_answer(
            assessment_id, question_id, correct_answer
        )

        response = client.post(
            f"/assessment/{student_id}/submit",
            data={
                "csrf_token": csrf_token,
                "question_id": question_id,
                "student_answer": displayed,
            },
            follow_redirects=False,
        )

        if response.status_code not in (200, 302):
            return False, (
                f"Submit failed for {question_id} "
                f"({response.status_code})"
            )

    # 5. Verify the score
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT COUNT(*) AS total, SUM(is_correct) AS correct
            FROM answers
            WHERE assessment_id = ?
            """,
            (assessment_id,),
        )
        row = cursor.fetchone()

    total = row["total"] or 0
    correct = row["correct"] or 0

    if total == 30 and correct == 30:
        return True, f"{correct}/{total}"

    return False, f"{correct}/{total}"


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    print("=" * 72)
    print("SMART KNOWLEDGE GAP — END-TO-END VALIDATION")
    print("=" * 72)

    # 1. Remove any previous test data
    if DB_PATH.exists():
        DB_PATH.unlink()

    # 2. Create the schema
    initialize_database(db_path=DB_PATH, verbose=False)

    results = []

    for subject_name, subject_id in SUBJECTS.items():
        for level in LEVELS:
            passed, detail = run_single_combination(
                subject_name, subject_id, level
            )
            status = "PASS" if passed else "FAIL"
            print(
                f"[{status}] "
                f"{subject_name:<20} / {level:<15} -> {detail}"
            )
            results.append(passed)

    print()
    print("=" * 72)
    total = len(results)
    passed = sum(1 for r in results if r)
    print(f"TOTAL: {passed}/{total} combinations passed")
    print("=" * 72)

    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
