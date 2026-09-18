import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pandas as pd
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

try:
    from .backend_service import BackendService
    from .repository import (
        load_question_bank,
        get_learning_content_for_concept,
        get_practice_for_concept
    )
    from .student_dashboard_service import get_student_dashboard_data
    from .teacher_dashboard_service import get_teacher_dashboard_data
    from .init_database import initialize_database, database_exists
except ImportError:
    from backend_service import BackendService
    from repository import (
        load_question_bank,
        get_learning_content_for_concept,
        get_practice_for_concept
    )
    from student_dashboard_service import get_student_dashboard_data
    from teacher_dashboard_service import get_teacher_dashboard_data
    from init_database import initialize_database, database_exists


app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable is required."
    )


# ============================================================
# LOGGING CONFIGURATION
# ============================================================

def configure_logging(flask_app):
    """
    Configure application logging.

    Logs to:
        - console (stdout) for development
        - a rotating file (logs/app.log) for production debugging
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    flask_app.logger.handlers.clear()
    flask_app.logger.addHandler(console_handler)
    flask_app.logger.addHandler(file_handler)
    flask_app.logger.setLevel(log_level)

    flask_app.logger.info(
        "Logging configured (level=%s, file=%s)",
        log_level, log_dir / "app.log"
    )


configure_logging(app)

# Ensure database schema exists before creating the service
if not database_exists():
    initialize_database(verbose=True)

service = BackendService()


OPTION_KEYS = ("A", "B", "C", "D")


def prepare_question_for_display(question, assessment_id):
    """
    Prepare a question for display using the same deterministic
    option mapping used by submit_answer().

    The original question-bank data is not modified.
    Only the displayed copy is reordered.
    """
    import copy

    prepared_question = copy.deepcopy(question)

    option_mapping = remember_option_mapping(
        assessment_id=assessment_id,
        question_id=prepared_question["question_id"]
    )

    original_options = {
        "A": prepared_question["option_a"],
        "B": prepared_question["option_b"],
        "C": prepared_question["option_c"],
        "D": prepared_question["option_d"]
    }

    displayed_options = {
        displayed: original_options[original]
        for displayed, original in option_mapping.items()
    }

    prepared_question["option_a"] = displayed_options["A"]
    prepared_question["option_b"] = displayed_options["B"]
    prepared_question["option_c"] = displayed_options["C"]
    prepared_question["option_d"] = displayed_options["D"]

    return prepared_question


def build_option_mapping(assessment_id, question_id):
    """
    Build a deterministic option mapping for a question.

    IMPORTANT:
    The mapping is derived from a STABLE seed that does NOT
    depend on app.secret_key. This guarantees that the mapping
    used at display time is IDENTICAL to the mapping used at
    submit time, even if the server restarts or the secret key
    changes.

    The mapping is also stored in the Flask session so that
    submit_answer() can retrieve EXACTLY the same mapping.
    """
    import hashlib

    seed = f"SKG::{assessment_id}::{question_id}::V1"

    ordered_options = sorted(
        OPTION_KEYS,
        key=lambda original: hashlib.sha256(
            f"{seed}::{original}".encode("utf-8")
        ).hexdigest()
    )

    return {
        displayed: original
        for displayed, original
        in zip(OPTION_KEYS, ordered_options)
    }


SESSION_MAPPINGS_KEY = "option_mappings"


MAX_SESSION_MAPPINGS = 200


def _cleanup_session_storage():
    """
    Keep the Flask session small.

    Removes the oldest option-mappings if the session grows
    beyond MAX_SESSION_MAPPINGS entries.
    """
    store = session.get(SESSION_MAPPINGS_KEY, {})

    if len(store) > MAX_SESSION_MAPPINGS:
        # Keep the most recent MAX_SESSION_MAPPINGS entries
        items = list(store.items())
        # Order in dict is insertion order in Python 3.7+
        recent = dict(items[-MAX_SESSION_MAPPINGS:])
        session[SESSION_MAPPINGS_KEY] = recent
        session.modified = True


def remember_option_mapping(assessment_id, question_id):
    """
    Compute the option mapping for a question and store it
    in the Flask session so that submit_answer() can reuse
    EXACTLY the same mapping.
    """
    mapping = build_option_mapping(
        assessment_id=assessment_id,
        question_id=question_id
    )

    store = session.get(SESSION_MAPPINGS_KEY, {})
    store[f"{assessment_id}:{question_id}"] = mapping
    session[SESSION_MAPPINGS_KEY] = store
    session.modified = True

    _cleanup_session_storage()

    return mapping


def get_remembered_option_mapping(assessment_id, question_id):
    """
    Retrieve the option mapping that was used when the question
    was displayed.

    Falls back to computing it deterministically if not present.
    """
    store = session.get(SESSION_MAPPINGS_KEY, {})
    key = f"{assessment_id}:{question_id}"

    if key in store:
        return store[key]

    return build_option_mapping(
        assessment_id=assessment_id,
        question_id=question_id
    )


SESSION_QUESTION_ORDER_KEY = "question_shuffle_order"
SESSION_SHUFFLE_SEED_KEY = "shuffle_seed"


def get_or_create_shuffle_seed(assessment_id):
    """
    Return a random seed for this assessment.

    A NEW random seed is generated the first time we see an
    assessment_id in this session, ensuring that every new
    assessment gets a different shuffle.
    """
    import secrets

    seeds = session.get(SESSION_SHUFFLE_SEED_KEY, {})
    key = str(assessment_id)

    if key not in seeds:
        seeds[key] = secrets.randbits(32)
        session[SESSION_SHUFFLE_SEED_KEY] = seeds
        session.modified = True

    return seeds[key]


def get_shuffled_question_ids(assessment_id, all_question_ids):
    """
    Return a shuffled list of question IDs for this assessment.

    The shuffle is TRULY random: a fresh random seed is generated
    per assessment, stored in the session, and used to shuffle
    the questions exactly once.
    """
    import random

    key = str(assessment_id)
    store = session.get(SESSION_QUESTION_ORDER_KEY, {})

    if key in store and len(store[key]) == len(all_question_ids):
        return store[key]

    seed = get_or_create_shuffle_seed(assessment_id)
    rng = random.Random(seed)

    shuffled = list(all_question_ids)
    rng.shuffle(shuffled)

    store[key] = shuffled
    session[SESSION_QUESTION_ORDER_KEY] = store
    session.modified = True

    # Bound the number of stored shuffle orders per session
    MAX_SESSION_SHUFFLES = 20
    if len(store) > MAX_SESSION_SHUFFLES:
        items = list(store.items())
        session[SESSION_QUESTION_ORDER_KEY] = dict(items[-MAX_SESSION_SHUFFLES:])
        session.modified = True

    return shuffled



@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register_student():
    full_name = request.form.get(
        "full_name",
        request.form.get("name", "")
    ).strip()

    age = request.form.get(
        "age",
        ""
    ).strip()

    subject = request.form.get(
        "subject",
        ""
    ).strip()

    level = request.form.get(
        "level",
        ""
    ).strip()

    if not full_name:
        return (
            render_template(
                "index.html",
                error="Student name is required."
            ),
            400
        )

    if len(full_name) > 120:
        return (
            render_template(
                "index.html",
                error="Student name is too long."
            ),
            400
        )

    student_id = service.register_student(
        full_name=full_name
    )

    session["student_age"] = age
    session["student_subject"] = subject
    session["student_level"] = level

    return redirect(
        url_for(
            "assessment",
            student_id=student_id
        )
    )


@app.route(
    "/assessment/<int:student_id>",
    methods=["GET"]
)
def assessment(student_id):
    try:
        from .database import get_student
    except ImportError:
        from database import get_student

    student = get_student(student_id)

    if student is None:
        return (
            "Student not found.",
            404
        )

    questions = load_question_bank()

    if questions.empty:
        return (
            "Question Bank is empty.",
            500
        )

    selected_subject = session.get("student_subject", "").strip()
    selected_level = session.get("student_level", "").strip()

    if selected_level:
        questions = questions[
            questions["difficulty"].astype(str).str.strip() == selected_level
        ].copy()

    subject_id_map = {
        "Mathematics": 1,
        "Physics": 2,
        "Computer Science": 3
    }

    if selected_subject:
        subject_id = subject_id_map.get(selected_subject)

        if subject_id is not None:
            questions = questions[
                questions["subject_id"] == subject_id
            ].copy()

    if questions.empty:
        return (
            "No questions are available for the selected subject and level.",
            400
        )

    questions = questions.sort_values(
        ["concept_id", "question_id"]
    ).reset_index(drop=True)

    assessment_id = session.get(
        "assessment_id"
    )

    assessment_student_id = session.get(
        "assessment_student_id"
    )

    if (
        assessment_id is None
        or assessment_student_id != student_id
    ):
        assessment_id = service.start_assessment(
            student_id=student_id,
            assessment_type="Diagnostic"
        )

        session["assessment_id"] = assessment_id
        session["assessment_student_id"] = student_id

    try:
        from .database import get_assessment_answers
    except ImportError:
        from database import get_assessment_answers

    answers = get_assessment_answers(
        assessment_id
    )

    answered_ids = {
        answer["question_id"]
        for answer in answers
    }

    # Apply shuffled order for this assessment
    all_qids = questions["question_id"].tolist()
    shuffled_qids = get_shuffled_question_ids(
        assessment_id, all_qids
    )

    questions = (
        questions
        .set_index("question_id")
        .loc[shuffled_qids]
        .reset_index()
    )

    remaining_questions = questions[
        ~questions["question_id"].isin(
            answered_ids
        )
    ]

    if remaining_questions.empty:
        # Redirect to the results route if available,
        # otherwise render the results inline.
        try:
            from .database import (
                get_concept_results_for_assessment
            )
        except ImportError:
            from database import (
                get_concept_results_for_assessment
            )

        diagnosis_records = (
            get_concept_results_for_assessment(
                assessment_id
            )
        )

        if diagnosis_records:
            diagnosis_df = pd.DataFrame(
                [
                    {
                        "concept_id": int(r["concept_id"]),
                        "mastery": float(r["mastery"]),
                        "gap_level": r["gap_level"],
                        "gap_score": float(r["gap_score"])
                    }
                    for r in diagnosis_records
                ]
            )

            concept_names = (
                questions[
                    ["concept_id", "concept_name"]
                ]
                .drop_duplicates("concept_id")
                .set_index("concept_id")["concept_name"]
            )

            diagnosis_df["concept_name"] = (
                diagnosis_df["concept_id"].map(concept_names)
            )

            priority_df = service.build_priority(
                diagnosis_df
            )

            learning_path_df = (
                service.build_learning_path(
                    diagnosis_df,
                    priority_df
                )
            )

            return render_template(
                "results.html",
                student_id=student_id,
                diagnosis=diagnosis_df.to_dict(
                    orient="records"
                ),
                priority=priority_df.to_dict(
                    orient="records"
                ),
                learning_path=learning_path_df.to_dict(
                    orient="records"
                )
            )

        return (
            "Diagnostic assessment completed.",
            200
        )

    question = (
        remaining_questions.iloc[0].to_dict()
    )

    question = prepare_question_for_display(
        question=question,
        assessment_id=assessment_id
    )

    return render_template(
        "assessment.html",
        question=question,
        question_number=len(answers) + 1,
        total_questions=len(questions),
        student_id=student_id,
        is_reassessment=False
    )


@app.route(
    "/reassessment/<int:student_id>",
    methods=["GET"]
)
def reassessment(student_id):

    try:
        from .database import (
            get_student,
            get_latest_diagnostic_assessment,
            get_concept_results_for_assessment
        )
    except ImportError:
        from database import (
            get_student,
            get_latest_diagnostic_assessment,
            get_concept_results_for_assessment
        )

    student = get_student(student_id)

    if student is None:
        return (
            "Student not found.",
            404
        )

    selected_subject = session.get(
        "student_subject",
        ""
    ).strip()

    selected_level = session.get(
        "student_level",
        ""
    ).strip()

    subject_id_map = {
        "Mathematics": 1,
        "Physics": 2,
        "Computer Science": 3
    }

    if selected_subject not in subject_id_map:
        return (
            "Subject selection is required before reassessment.",
            400
        )

    if selected_level not in {
        "Beginner",
        "Intermediate",
        "Advanced"
    }:
        return (
            "Level selection is required before reassessment.",
            400
        )

    diagnostic = (
        get_latest_diagnostic_assessment(
            student_id
        )
    )

    if diagnostic is None:
        return (
            "No completed Diagnostic assessment was found.",
            404
        )

    before_results = (
        get_concept_results_for_assessment(
            diagnostic["assessment_id"]
        )
    )

    if not before_results:
        return (
            "Diagnostic mastery results were not found.",
            409
        )

    expected_subject_id = (
        subject_id_map[selected_subject]
    )

    questions = load_question_bank()

    questions = questions[
        (
            questions["subject_id"]
            == expected_subject_id
        )
        & (
            questions["difficulty"]
            .astype(str)
            .str.strip()
            == selected_level
        )
    ].copy()

    if len(questions) != 30:
        return (
            "Reassessment question set is invalid.",
            500
        )

    current_concepts = set(
        questions["concept_id"]
        .astype(int)
        .tolist()
    )

    diagnostic_concepts = {
        int(item["concept_id"])
        for item in before_results
    }

    if current_concepts != diagnostic_concepts:
        return (
            "The selected subject and level do not match "
            "the previous Diagnostic assessment.",
            409
        )

    reassessment_id = service.start_assessment(
        student_id=student_id,
        assessment_type="Reassessment"
    )

    session["reassessment_id"] = (
        reassessment_id
    )

    session["reassessment_student_id"] = (
        student_id
    )


    session["reassessment_diagnostic_id"] = (
        diagnostic["assessment_id"]
    )

    session["reassessment_subject"] = (
        selected_subject
    )

    session["reassessment_level"] = (
        selected_level
    )

    questions = questions.sort_values(
        ["concept_id", "question_id"]
    ).reset_index(drop=True)

    question = (
        questions.iloc[0].to_dict()
    )

    question = prepare_question_for_display(
        question=question,
        assessment_id=reassessment_id
    )

    return render_template(
        "assessment.html",
        question=question,
        question_number=1,
        total_questions=30,
        student_id=student_id,
        is_reassessment=True
    )


@app.route(
    "/learning/<int:concept_id>",
    methods=["GET"]
)
def learning_content(concept_id):
    content = get_learning_content_for_concept(
        concept_id
    )

    if content is None:
        return (
            "Learning content not found.",
            404
        )

    student_id = request.args.get(
        "student_id",
        type=int
    )

    return render_template(
        "learning_content.html",
        content=content,
        student_id=student_id
    )



@app.route(
    "/practice/<int:student_id>/<int:concept_id>",
    methods=["GET", "POST"]
)
def practice(student_id, concept_id):

    practice_questions = get_practice_for_concept(
        concept_id
    )

    if practice_questions.empty:
        return (
            "Practice questions not found.",
            404
        )

    if len(practice_questions) != 6:
        return (
            "Practice question set is invalid.",
            500
        )

    if request.method == "GET":

        return render_template(
            "practice.html",
            student_id=student_id,
            concept_id=concept_id,
            concept_name=(
                practice_questions.iloc[0]["concept_name"]
            ),
            difficulty=(
                practice_questions.iloc[0]["difficulty"]
            ),
            questions=practice_questions.to_dict(
                orient="records"
            )
        )

    try:
        from .database import save_practice_attempt
    except ImportError:
        from database import save_practice_attempt

    results = []

    for _, question in practice_questions.iterrows():

        question_id = str(
            question["question_id"]
        )

        student_answer = request.form.get(
            f"answer_{question_id}",
            ""
        ).strip().upper()

        correct_answer = str(
            question["correct_answer"]
        ).strip().upper()

        is_correct = (
            student_answer == correct_answer
            and bool(student_answer)
        )

        score = (
            100.0
            if is_correct
            else 0.0
        )

        save_practice_attempt(
            student_id=student_id,
            question_id=question_id,
            student_answer=student_answer,
            is_correct=is_correct,
            score=score
        )

        results.append(
            {
                "question_id": question_id,
                "is_correct": is_correct,
                "score": score
            }
        )

    correct_count = sum(
        1
        for item in results
        if item["is_correct"]
    )

    total_questions = len(results)

    accuracy = (
        correct_count / total_questions * 100
        if total_questions
        else 0.0
    )

    return render_template(
        "practice.html",
        student_id=student_id,
        concept_id=concept_id,
        concept_name=(
            practice_questions.iloc[0]["concept_name"]
        ),
        difficulty=(
            practice_questions.iloc[0]["difficulty"]
        ),
        questions=practice_questions.to_dict(
            orient="records"
        ),
        results=results,
        correct_count=correct_count,
        total_questions=total_questions,
        accuracy=accuracy,
        completed=True
    )


@app.route(
    "/dashboard/<int:student_id>",
    methods=["GET"]
)
def student_dashboard(student_id):
    try:
        dashboard_data = get_student_dashboard_data(
            student_id
        )
    except ValueError as exc:
        return (
            str(exc),
            404
        )
    except Exception as exc:
        app.logger.exception(
            "Student dashboard failed for student_id=%s",
            student_id
        )
        return (
            "Unable to load the student dashboard.",
            500
        )

    return render_template(
        "student_dashboard.html",
        **dashboard_data
    )


@app.route(
    "/teacher-dashboard",
    methods=["GET"]
)
def teacher_dashboard():
    try:
        dashboard_data = get_teacher_dashboard_data()
    except Exception:
        app.logger.exception(
            "Teacher dashboard failed."
        )
        return (
            "Unable to load the teacher dashboard.",
            500
        )

    return render_template(
        "teacher_dashboard.html",
        **dashboard_data
    )



@app.route(
    "/assessment/<int:student_id>/submit",
    methods=["POST"]
)
def submit_answer(student_id):
    reassessment_id = session.get(
        "reassessment_id"
    )
    reassessment_student_id = session.get(
        "reassessment_student_id"
    )

    if (
        reassessment_id is not None
        and reassessment_student_id == student_id
    ):
        assessment_id = reassessment_id
        is_reassessment = True
    else:
        assessment_id = session.get(
            "assessment_id"
        )
        assessment_student_id = session.get(
            "assessment_student_id"
        )

        if (
            assessment_id is None
            or assessment_student_id != student_id
        ):
            return (
                "Assessment session is invalid.",
                400
            )

        is_reassessment = False

    question_id = request.form.get(
        "question_id",
        ""
    ).strip()

    student_answer = request.form.get(
        "student_answer",
        ""
    ).strip().upper()

    if not question_id:
        return (
            "Question ID is required.",
            400
        )

    if student_answer not in {"A", "B", "C", "D"}:
        return (
            "A valid answer is required.",
            400
        )

    try:
        from .database import get_assessment_answers
    except ImportError:
        from database import get_assessment_answers

    existing_answers = get_assessment_answers(
        assessment_id
    )

    answered_ids = {
        answer["question_id"]
        for answer in existing_answers
    }

    if question_id in answered_ids:
        return (
            "This question has already been answered.",
            400
        )

    question_mapping = get_remembered_option_mapping(
        assessment_id=assessment_id,
        question_id=question_id
    )

    original_answer = question_mapping.get(
        student_answer
    )

    if original_answer not in {"A", "B", "C", "D"}:
        return (
            "Assessment option mapping is invalid.",
            400
        )

    result = service.score_answer(
        question_id=question_id,
        student_answer=original_answer
    )

    service.persist_answer(
        assessment_id=assessment_id,
        student_answer_result=result,
        student_answer=student_answer
    )

    answers = get_assessment_answers(
        assessment_id
    )

    questions = load_question_bank()

    selected_subject = session.get(
        "student_subject",
        ""
    ).strip()

    selected_level = session.get(
        "student_level",
        ""
    ).strip()

    subject_id_map = {
        "Mathematics": 1,
        "Physics": 2,
        "Computer Science": 3
    }

    if selected_subject not in subject_id_map:
        return (
            "Invalid subject selection.",
            400
        )

    if selected_level not in {
        "Beginner",
        "Intermediate",
        "Advanced"
    }:
        return (
            "Invalid level selection.",
            400
        )

    questions = questions[
        questions["subject_id"] == subject_id_map[
            selected_subject
        ]
    ].copy()

    questions = questions[
        questions["difficulty"].astype(str).str.strip()
        == selected_level
    ].copy()

    if len(questions) != 30:
        return (
            "Assessment question set is invalid.",
            500
        )

    # Apply the SAME shuffled order used in assessment()
    all_qids = questions["question_id"].tolist()
    shuffled_qids = get_shuffled_question_ids(
        assessment_id, all_qids
    )

    questions = (
        questions
        .set_index("question_id")
        .loc[shuffled_qids]
        .reset_index()
    )

    answered_ids = {
        answer["question_id"]
        for answer in answers
    }

    remaining_questions = questions[
        ~questions["question_id"].isin(
            answered_ids
        )
    ]

    if remaining_questions.empty:
        diagnosis_records = []

        answers_df = pd.DataFrame(
            answers
        )

        for concept_id in sorted(
            questions["concept_id"].unique()
        ):
            concept_result = service.calculate_mastery(
                concept_id=concept_id,
                answers_df=answers_df
            )

            diagnosis_records.append(
                concept_result
            )

        diagnosis_df = pd.DataFrame(
            diagnosis_records
        )

        concept_names = (
            questions[
                ["concept_id", "concept_name"]
            ]
            .drop_duplicates("concept_id")
            .set_index("concept_id")[
                "concept_name"
            ]
            .to_dict()
        )

        diagnosis_df["concept_name"] = (
            diagnosis_df["concept_id"]
            .map(concept_names)
        )

        if diagnosis_df["concept_name"].isna().any():
            raise RuntimeError(
                "Concept name mapping failed."
            )

        if is_reassessment:
            diagnostic_id = session.get(
                "reassessment_diagnostic_id"
            )

            if diagnostic_id is None:
                return (
                    "Reassessment Diagnostic reference is missing.",
                    409
                )

            try:
                from .database import (
                    get_concept_results_for_assessment,
                    save_reassessment
                )
            except ImportError:
                from database import (
                    get_concept_results_for_assessment,
                    save_reassessment
                )

            before_results = (
                get_concept_results_for_assessment(
                    diagnostic_id
                )
            )

            if not before_results:
                return (
                    "Diagnostic mastery results were not found.",
                    409
                )

            before_by_concept = {
                int(record["concept_id"]): float(
                    record["mastery"]
                )
                for record in before_results
            }

            current_concepts = {
                int(concept_id)
                for concept_id in diagnosis_df[
                    "concept_id"
                ].tolist()
            }

            before_concepts = set(
                before_by_concept.keys()
            )

            if current_concepts != before_concepts:
                return (
                    "Diagnostic and Reassessment concepts do not match.",
                    409
                )

            for record in diagnosis_records:
                concept_id = int(
                    record["concept_id"]
                )

                before_mastery = (
                    before_by_concept[concept_id]
                )

                after_mastery = float(
                    record["mastery"]
                )

                improvement = (
                    after_mastery
                    - before_mastery
                )

                save_reassessment(
                    student_id=student_id,
                    concept_id=concept_id,
                    before_mastery=before_mastery,
                    after_mastery=after_mastery,
                    improvement=improvement
                )

            priority_df = service.build_priority(
                diagnosis_df
            )

            learning_path_df = (
                service.build_learning_path(
                    diagnosis_df,
                    priority_df
                )
            )

            return render_template(
                "results.html",
                student_id=student_id,
                diagnosis=diagnosis_df.to_dict(
                    orient="records"
                ),
                priority=priority_df.to_dict(
                    orient="records"
                ),
                learning_path=learning_path_df.to_dict(
                    orient="records"
                ),
                reassessment_completed=True,
                before_mastery=before_by_concept,
                after_mastery={
                    int(record["concept_id"]):
                    float(record["mastery"])
                    for record in diagnosis_records
                }
            )

        for record in diagnosis_records:
            service.persist_concept_result(
                assessment_id=assessment_id,
                concept_result=record
            )

        priority_df = service.build_priority(
            diagnosis_df
        )

        learning_path_df = (
            service.build_learning_path(
                diagnosis_df,
                priority_df
            )
        )

        return render_template(
            "results.html",
            student_id=student_id,
            diagnosis=diagnosis_df.to_dict(
                orient="records"
            ),
            priority=priority_df.to_dict(
                orient="records"
            ),
            learning_path=learning_path_df.to_dict(
                orient="records"
            )
        )

    next_question = (
        remaining_questions.iloc[0].to_dict()
    )

    next_question = prepare_question_for_display(
        question=next_question,
        assessment_id=assessment_id
    )

    return render_template(
        "assessment.html",
        question=next_question,
        question_number=len(answers) + 1,
        total_questions=len(questions),
        student_id=student_id,
        is_reassessment=is_reassessment
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 Not Found errors."""
    app.logger.warning(
        "404 Not Found: %s",
        request.path
    )
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    app.logger.error(
        "500 Internal Server Error on %s",
        request.path,
        exc_info=True
    )
    return render_template("500.html"), 500


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """
    Handle unexpected exceptions.

    In debug mode, we let Flask show the standard debugger.
    In production, we log the error and show a friendly 500 page.
    """
    # Let HTTPExceptions pass through
    from werkzeug.exceptions import HTTPException

    if isinstance(error, HTTPException):
        return error

    app.logger.exception(
        "Unexpected error on %s: %s",
        request.path,
        str(error)
    )
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
