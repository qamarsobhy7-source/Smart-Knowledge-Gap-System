import os
import pandas as pd
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from backend_service import BackendService
from repository import load_question_bank
from student_dashboard_service import get_student_dashboard_data
from teacher_dashboard_service import get_teacher_dashboard_data


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

service = BackendService()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register_student():
    full_name = request.form.get(
        "full_name",
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
    questions = load_question_bank()

    if questions.empty:
        return (
            "Question Bank is empty.",
            500
        )

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

    from database import get_assessment_answers

    answers = get_assessment_answers(
        assessment_id
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
        return (
            "Diagnostic assessment completed.",
            200
        )

    question = (
        remaining_questions.iloc[0].to_dict()
    )

    return render_template(
        "assessment.html",
        question=question,
        question_number=len(answers) + 1,
        total_questions=len(questions),
        student_id=student_id
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
    assessment_id = session.get("assessment_id")
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

    result = service.score_answer(
        question_id=question_id,
        student_answer=student_answer
    )

    service.persist_answer(
        assessment_id=assessment_id,
        student_answer_result=result,
        student_answer=student_answer
    )

    from database import get_assessment_answers

    answers = get_assessment_answers(
        assessment_id
    )

    questions = load_question_bank()

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

    return render_template(
        "assessment.html",
        question=next_question,
        question_number=len(answers) + 1,
        total_questions=len(questions),
        student_id=student_id
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
