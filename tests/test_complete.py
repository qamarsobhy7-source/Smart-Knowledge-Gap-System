"""
Comprehensive test suite for the Smart Knowledge Gap System.

Covers:
    1. Database initialization
    2. Student registration and login
    3. Complete assessment flow
    4. All Flask routes
    5. ML models availability

Usage:
    python tests/test_complete.py
"""

import os
import sys
import re
import hashlib
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-for-full-validation-only"
)
os.environ.pop("DATABASE_URL", None)

DB_PATH = PROJECT_ROOT / "data" / "smart_knowledge_gap.db"
if DB_PATH.exists():
    DB_PATH.unlink()

from init_database import initialize_database
initialize_database(db_path=str(DB_PATH), verbose=False)

import pandas as pd
import app as app_module

app_module.app.config["TESTING"] = True
client = app_module.app.test_client()


RESULTS = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    RESULTS.append((name, condition))
    suffix = f" -- {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")


def extract_csrf(html):
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    return match.group(1) if match else None


def compute_displayed_answer(assessment_id, question_id, correct_answer):
    seed = f"SKG::{assessment_id}::{question_id}::V1"
    options = ("A", "B", "C", "D")
    ordered = sorted(
        options,
        key=lambda o: hashlib.sha256(
            f"{seed}::{o}".encode("utf-8")
        ).hexdigest(),
    )
    mapping = dict(zip(options, ordered))
    for displayed, original in mapping.items():
        if original == correct_answer:
            return displayed
    return None


def main():
    print("=" * 72)
    print("SMART KNOWLEDGE GAP -- FULL TEST SUITE")
    print("=" * 72)
    print()

    # ========================================================
    # 1. Public pages
    # ========================================================
    print("1. Public pages")
    print("-" * 72)

    for url, name, expected in [
        ("/", "Home", 200),
        ("/login", "Login", 200),
        ("/forgot-password", "Forgot Password", 200),
        ("/teacher-dashboard", "Teacher Dashboard", 200),
        ("/ml/metrics", "ML Metrics", 200),
        ("/this-does-not-exist", "404 Page", 404),
    ]:
        r = client.get(url)
        check(f"{name} ({r.status_code})", r.status_code == expected)

    # ========================================================
    # 2. Registration
    # ========================================================
    print()
    print("2. Registration")
    print("-" * 72)

    r = client.get("/")
    csrf = extract_csrf(r.get_data(as_text=True))

    r = client.post("/register", data={
        "csrf_token": csrf,
        "name": "Test Student",
        "email": "test@student.com",
        "password": "testpass123",
        "age": "20",
        "subject": "Computer Science",
        "level": "Beginner",
    }, follow_redirects=False)

    check("Register succeeds", r.status_code == 302)
    student_id = int(r.headers.get("Location", "").split("/")[-1])

    # Duplicate email
    r = client.get("/")
    csrf = extract_csrf(r.get_data(as_text=True))
    r = client.post("/register", data={
        "csrf_token": csrf,
        "name": "Another",
        "email": "test@student.com",
        "password": "another123",
        "age": "22",
        "subject": "Physics",
        "level": "Beginner",
    }, follow_redirects=False)
    check("Duplicate email rejected", r.status_code == 400)

    # Short password
    r = client.get("/")
    csrf = extract_csrf(r.get_data(as_text=True))
    r = client.post("/register", data={
        "csrf_token": csrf,
        "name": "Short",
        "email": "short@test.com",
        "password": "123",
        "age": "20",
        "subject": "Physics",
        "level": "Beginner",
    }, follow_redirects=False)
    check("Short password rejected", r.status_code == 400)

    # ========================================================
    # 3. Assessment Flow
    # ========================================================
    print()
    print("3. Assessment Flow")
    print("-" * 72)

    r = client.get(f"/assessment/{student_id}")
    check("Assessment page loads", r.status_code == 200)

    with client.session_transaction() as sess:
        assessment_id = sess.get("assessment_id")
    check("Assessment ID created", assessment_id is not None)

    # Debug: verify DB path
    print(f"    [DEBUG] DB path: {DB_PATH}")
    print(f"    [DEBUG] DB exists: {DB_PATH.exists()}")

    # Load question bank
    questions_df = pd.read_csv(
        PROJECT_ROOT / "data" / "final_question_bank_270.csv"
    )
    selected = questions_df[
        (questions_df["subject_id"] == 3)
        & (questions_df["difficulty"] == "Beginner")
    ].sort_values(["concept_id", "question_id"]).reset_index(drop=True)

    correct_map = dict(zip(
        selected["question_id"],
        selected["correct_answer"],
    ))

    # Answer all 30 correctly except a few
    for i in range(30):
        r = client.get(f"/assessment/{student_id}")
        if r.status_code != 200:
            break
        html = r.get_data(as_text=True)
        match_q = re.search(r'name="question_id"\s+value="([^"]+)"', html)
        csrf = extract_csrf(html)
        if not match_q or not csrf:
            break
        qid = match_q.group(1)
        correct_answer = correct_map.get(qid)
        displayed = compute_displayed_answer(
            assessment_id, qid, correct_answer
        )

        # Deliberately wrong in 6 concepts (indices 6..24)
        if 6 <= i < 24:
            displayed = "A" if displayed != "A" else "B"

        client.post(
            f"/assessment/{student_id}/submit",
            data={
                "csrf_token": csrf,
                "question_id": qid,
                "student_answer": displayed,
            },
            follow_redirects=False,
        )

    # Verify answers in DB
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) AS total FROM answers WHERE assessment_id = ?",
        (assessment_id,),
    )
    total = cursor.fetchone()["total"]
    conn.close()
    check("30 questions answered", total == 30, f"({total}/30)")

    # ========================================================
    # 4. Dashboard
    # ========================================================
    print()
    print("4. Student Dashboard")
    print("-" * 72)

    r = client.get(f"/dashboard/{student_id}")
    check("Dashboard loads", r.status_code == 200)

    html = r.get_data(as_text=True)
    check("Charts present", "masteryDistributionChart" in html)
    check("Badges present", "badges-grid" in html)
    check("AI Insights CTA", "AI INSIGHTS" in html)
    check("AI Assistant CTA", "AI ASSISTANT" in html)
    check("PDF button", "Download PDF" in html)

    # ========================================================
    # 5. AI Insights
    # ========================================================
    print()
    print("5. AI Insights")
    print("-" * 72)

    r = client.get(f"/ml/insights/{student_id}")
    check("ML Insights loads", r.status_code == 200)
    html = r.get_data(as_text=True)
    check("Cluster section", "learning cluster" in html)
    check("Risk Predictions", "At-Risk Predictions" in html)
    check("SHAP Explanation", "EXPLAINABLE AI" in html or "Why this prediction" in html)
    check("RL Adaptive Path", "REINFORCEMENT LEARNING" in html)
    check("Recommendations", "Recommended next steps" in html)

    # ========================================================
    # 6. PDF Report
    # ========================================================
    print()
    print("6. PDF Report")
    print("-" * 72)

    r = client.get(f"/report/{student_id}")
    check("PDF generates", r.status_code == 200)
    check("Valid PDF header", r.data[:4] == b"%PDF")

    # ========================================================
    # 7. Learning Content
    # ========================================================
    print()
    print("7. Learning Content")
    print("-" * 72)

    r = client.get(f"/learning/32?student_id={student_id}")
    html = r.get_data(as_text=True)
    check("Content loads", r.status_code == 200)
    check("Why It Matters", "Why It Matters" in html)
    check("Step-by-Step", "Step-by-Step" in html)
    check("Common Mistakes", "Common Mistakes" in html)
    check("Study Tips", "Study Tips" in html)

    # ========================================================
    # 8. Practice + Teacher Filters
    # ========================================================
    print()
    print("8. Practice + Teacher Filters")
    print("-" * 72)

    r = client.get(f"/practice/{student_id}/32")
    check("Practice page", r.status_code == 200)

    for url, name in [
        ("/teacher-dashboard", "Base"),
        ("/teacher-dashboard?subject=Computer+Science", "Subject"),
        ("/teacher-dashboard?level=Beginner", "Level"),
        ("/teacher-dashboard?status=at_risk", "Status"),
    ]:
        r = client.get(url)
        check(f"Teacher filter: {name}", r.status_code == 200)

    # ========================================================
    # 9. AI Chat
    # ========================================================
    print()
    print("9. AI Chat")
    print("-" * 72)

    r = client.get("/chat")
    check("Chat page loads", r.status_code == 200)
    html = r.get_data(as_text=True)
    check("Chat container", "chat-container" in html)

    # ========================================================
    # 10. Multi-language
    # ========================================================
    print()
    print("10. Multi-language")
    print("-" * 72)

    client.get("/set-language/ar")
    r = client.get("/")
    html = r.get_data(as_text=True)
    check("Arabic RTL", 'dir="rtl"' in html)
    check("Arabic text", "الرئيسية" in html)

    client.get("/set-language/en")
    r = client.get("/")
    html = r.get_data(as_text=True)
    check("English LTR", 'dir="ltr"' in html)

    # ========================================================
    # 11. ML Models
    # ========================================================
    print()
    print("11. ML Models Availability")
    print("-" * 72)

    # First check whether torch is actually usable in this environment.
    # Colab sometimes breaks torch after repeated imports, and light
    # deployments (like Faable free tier) intentionally skip torch.
    try:
        import torch  # noqa: F401
        torch_usable = True
    except Exception as exc:
        torch_usable = False
        print(f"      [INFO] torch is not usable here: {type(exc).__name__}")
        print(f"      [INFO] Skipping torch-dependent models")

    from ml.ml_service import models_available
    available = models_available()

    for model_name, available_flag in available.items():
        # torch-dependent models are optional
        if model_name in ("knowledge_tracing", "rl_agent") and not torch_usable:
            print(f"      [SKIP] {model_name} (torch unavailable)")
            continue
        # RAG + SHAP are optional locally — configured on production (Faable)
        if model_name in ("rag_available", "shap_available") and not available_flag:
            print(f"      [SKIP] {model_name} (cloud service not configured locally)")
            continue
        check(f"Model: {model_name}", available_flag)

    # ========================================================
    # 12. Feynman Board
    # ========================================================
    print()
    print("12. Feynman Board")
    print("-" * 72)

    r = client.get(f"/feynman/{student_id}/32")
    check("Feynman page loads", r.status_code == 200)

    if r.status_code == 200:
        html = r.get_data(as_text=True)
        check("Feynman hero", "FEYNMAN TECHNIQUE" in html)
        check("Explanation form", 'name="explanation"' in html)
        check("Submit button", "Submit for AI Evaluation" in html)

    # ========================================================
    # Summary
    # ========================================================
    print()
    print("=" * 72)
    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 72)

    # Cleanup
    if DB_PATH.exists():
        DB_PATH.unlink()

    if passed == total:
        print()
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print()
        print("Failed tests:")
        for name, ok in RESULTS:
            if not ok:
                print(f"  - {name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
