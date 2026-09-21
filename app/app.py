import os
import logging
import sys
import secrets
import hmac
from datetime import datetime, timedelta
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

import pandas as pd
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    abort,
    g
)

# === Rate Limiting (اختياري) ===
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    Limiter = None
    get_remote_address = None


# Check optional AI libraries (some deployments may skip them)
import importlib.util

def _has_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False

AI_HEAVY_AVAILABLE = all([
    _has_module("torch"),
    _has_module("qdrant_client"),
    _has_module("sentence_transformers"),
])

try:
    from .backend_service import BackendService
    from .repository import (
        load_question_bank,
        load_concepts,
        get_learning_content_for_concept,
        get_practice_for_concept
    )
    from .student_dashboard_service import get_student_dashboard_data
    from .teacher_dashboard_service import get_teacher_dashboard_data
    from .init_database import initialize_database, database_exists
    from .pdf_report import generate_student_report
    from .translations import get_text, SUPPORTED_LANGUAGES
except ImportError:
    from backend_service import BackendService
    from repository import (
        load_question_bank,
        load_concepts,
        get_learning_content_for_concept,
        get_practice_for_concept
    )
    from student_dashboard_service import get_student_dashboard_data
    from teacher_dashboard_service import get_teacher_dashboard_data
    from init_database import initialize_database, database_exists
    from pdf_report import generate_student_report
    from translations import get_text, SUPPORTED_LANGUAGES


# ============================================================
# OPTIONAL ML/LLM IMPORTS (safe fallbacks)
# ============================================================

try:
    from .ml.ml_service import (
        models_available,
        predict_student_risk,
        predict_student_cluster,
        recommend_concepts,
        get_model_metrics,
        explain_risk,
        explain_performance,
        plan_adaptive_path,
    )
except ImportError:
    try:
        from ml.ml_service import (
            models_available,
            predict_student_risk,
            predict_student_cluster,
            recommend_concepts,
            get_model_metrics,
            explain_risk,
            explain_performance,
            plan_adaptive_path,
        )
    except Exception:
        # Safe stubs
        def models_available():
            return {}

        def predict_student_risk(features):
            return None

        def predict_student_cluster(features):
            return None

        def recommend_concepts(*args, **kwargs):
            return []

        def get_model_metrics():
            return {}

        def explain_risk(features):
            return None

        def explain_performance(features):
            return None

        def plan_adaptive_path(*args, **kwargs):
            return []


try:
    from .ml.llm_service import (
        chat as llm_chat,
        is_available as llm_is_available,
        evaluate_feynman_explanation,
    )
except ImportError:
    try:
        from ml.llm_service import (
            chat as llm_chat,
            is_available as llm_is_available,
            evaluate_feynman_explanation,
        )
    except Exception:
        # Safe stubs
        def llm_chat(*args, **kwargs):
            return {
                "answer": None,
                "sources": [],
                "error": "AI assistant is not configured.",
            }

        def llm_is_available():
            return False

        def evaluate_feynman_explanation(*args, **kwargs):
            return {
                "score": 0.0,
                "feedback": "AI evaluation is not available.",
                "strengths": "",
                "gaps": "",
                "suggestions": "",
                "error": "LLM not configured.",
            }


app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

# ---- Session configuration for HTTPS ----
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
# -----------------------------------------

app.secret_key = os.environ.get("SECRET_KEY")

# === Rate Limiter Initialization ===
if LIMITER_AVAILABLE:
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "60 per hour"],
        storage_uri="memory://",
        strategy="fixed-window",
        enabled=not app.config.get("TESTING", False),
    )
else:
    # Fallback: dummy limiter (لا يعمل rate limiting، بس مش بيكسر الكود)
    class _DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    limiter = _DummyLimiter()


# ============================================================
# SECURITY HEADERS
# ============================================================
@app.after_request
def add_security_headers(response):
    """Add HTTP security headers to every response."""
    # Prevent MIME-type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    # Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Restrict browser features
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # HSTS — only when serving over HTTPS
    if request.is_secure or request.headers.get("X-Forwarded-Proto") == "https":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response



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


# ============================================================
# CSRF PROTECTION
# ============================================================

CSRF_SESSION_KEY = "_csrf_token"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


def generate_csrf_token():
    """Generate or retrieve the CSRF token for the current session."""
    if CSRF_SESSION_KEY not in session:
        session[CSRF_SESSION_KEY] = secrets.token_urlsafe(32)
        session.modified = True
    return session[CSRF_SESSION_KEY]


def validate_csrf_token(token):
    """Validate a submitted CSRF token against the session token."""
    session_token = session.get(CSRF_SESSION_KEY)
    if not session_token or not token:
        return False
    return hmac.compare_digest(session_token, token)


@app.before_request
def csrf_protect():
    """
    Validate CSRF tokens on all state-changing requests
    (POST, PUT, PATCH, DELETE).

    Skips requests that have no session yet (e.g. first visit).
    """
    if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
        return

    # If there's no session token yet, we cannot validate.
    # This handles the very first POST that establishes the session.
    if CSRF_SESSION_KEY not in session:
        return

    submitted_token = (
        request.form.get(CSRF_FORM_FIELD)
        or request.headers.get(CSRF_HEADER_NAME)
    )

    if not validate_csrf_token(submitted_token):
        app.logger.warning(
            "CSRF validation failed for %s %s",
            request.method,
            request.path
        )
        abort(400, description="CSRF validation failed.")


@app.context_processor
def inject_csrf_token():
    """Make csrf_token() available inside all Jinja templates."""
    return {
        "csrf_token": generate_csrf_token,
        "csrf_field_name": CSRF_FORM_FIELD,
    }


# ============================================================
# INTERNATIONALIZATION (i18n)
# ============================================================

DEFAULT_LANGUAGE = "en"
LANGUAGE_SESSION_KEY = "language"


def get_current_language():
    """Return the current language code from the session."""
    lang = session.get(LANGUAGE_SESSION_KEY, DEFAULT_LANGUAGE)
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    return lang


def is_rtl():
    """Return True if the current language uses RTL direction."""
    return get_current_language() == "ar"


def t(key, default=None):
    """Translate a key in the current language."""
    return get_text(get_current_language(), key, default)


@app.context_processor
def inject_i18n():
    """Make t() and language info available in all templates."""
    lang = get_current_language()
    return {
        "t": t,
        "current_language": lang,
        "supported_languages": SUPPORTED_LANGUAGES,
        "is_rtl": is_rtl(),
        "language_name": {
            "en": "English",
            "ar": "العربية",
        },
    }


# ============================================================
# PERFORMANCE TIMING MIDDLEWARE
# ============================================================
@app.before_request
def _start_timer():
    """Record request start time."""
    from time import time as _t
    g._perf_start = _t()


@app.after_request
def _log_perf(response):
    """Log request duration and add X-Response-Time header."""
    try:
        from time import time as _t
        start = getattr(g, "_perf_start", None)
        if start is not None:
            duration_ms = (_t() - start) * 1000
            response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

            # نسجل بس لو وقت الاستجابة > 100ms أو الـ DEBUG
            if duration_ms > 100:
                app.logger.info(
                    "PERF: %s %s -> %s (%.1fms)",
                    request.method,
                    request.path,
                    response.status_code,
                    duration_ms,
                )
    except Exception:
        pass
    return response


@app.route("/api/version", methods=["GET"])
def api_version():
    """Return API version and basic build info."""
    import time as _time
    from datetime import datetime as _dt

    return {
        "name": "Smart Knowledge Gap System",
        "version": "1.0.7",
        "api_version": "v1",
        "build_date": "2026-09-21",
        "environment": os.environ.get("FLASK_ENV", "production"),
        "python_version": "3.11.3",
        "framework": "Flask 3.1",
        "timestamp": int(_time.time()),
        "datetime": _dt.utcnow().isoformat() + "Z",
        "links": {
            "github": "https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System",
            "demo": "https://smart-knowledge-gap-system-qqbms.faable.link",
            "video": "https://qamarsobhy7-source.github.io/Smart-Knowledge-Gap-System/",
        },
    }


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring and load balancers.

    Checks all critical services (DB, Qdrant, Groq, ML models).
    Always returns 200 with detailed status per service.
    """
    import time as _time
    from datetime import datetime as _dt

    services = {}

    # 1. Database
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        # PostgreSQL (Supabase Cloud)
        services["database"] = {
            "status": "connected",
            "type": "postgresql",
        }
    else:
        # SQLite (local)
        try:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "smart_knowledge_gap.db"
            )
            services["database"] = {
                "status": "connected" if os.path.exists(db_path) else "missing",
                "type": "sqlite",
            }
        except Exception as exc:
            services["database"] = {"status": "error", "error": str(exc)[:100]}

    # 2. Qdrant (Vector DB)
    services["qdrant"] = {
        "status": "configured" if os.environ.get("QDRANT_URL") else "not_configured",
    }

    # 3. Groq (LLM)
    services["groq"] = {
        "status": "configured" if os.environ.get("GROQ_API_KEY") else "not_configured",
    }

    # 4. ML Models
    try:
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
        if os.path.exists(models_dir):
            model_files = [f for f in os.listdir(models_dir) if f.endswith((".joblib", ".pt"))]
            services["ml_models"] = {
                "status": "loaded",
                "count": len(model_files),
            }
        else:
            services["ml_models"] = {"status": "missing", "path": models_dir}
    except Exception as exc:
        services["ml_models"] = {"status": "error", "error": str(exc)[:100]}

    # 5. Overall status
    critical_ok = services.get("database", {}).get("status") == "connected"
    overall = "healthy" if critical_ok else "degraded"

    return {
        "status": overall,
        "service": "smart-knowledge-gap-system",
        "version": "1.0.7",
        "timestamp": int(_time.time()),
        "datetime": _dt.utcnow().isoformat() + "Z",
        "services": services,
    }


@app.route("/set-language/<lang>", methods=["GET"])
def set_language(lang):
    """Change the current language and redirect back."""
    if lang in SUPPORTED_LANGUAGES:
        session[LANGUAGE_SESSION_KEY] = lang
        session.modified = True

    # Redirect back to where the user came from
    next_url = request.args.get("next") or request.referrer or "/"
    return redirect(next_url)


# ============================================================
# AUTH HELPERS
# ============================================================

def login_required(f):
    """Decorator: require a logged-in student."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "student_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function


def current_student_id():
    """Return the currently logged-in student ID."""
    return session.get("student_id")


@app.context_processor
def inject_current_student():
    """Make the current student available in all templates."""
    return {
        "current_student_id": current_student_id(),
        "current_student_name": session.get("student_name"),
    }

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

    current_set = set(all_question_ids)

    if key in store:
        stored = store[key]
        # Only reuse the stored order if the IDs match EXACTLY.
        # This prevents stale orders from a previous student/level
        # from leaking into a new assessment.
        if (
            len(stored) == len(all_question_ids)
            and set(stored) == current_set
        ):
            return stored
        # Drop stale entry
        store.pop(key, None)
        session[SESSION_QUESTION_ORDER_KEY] = store
        session.modified = True

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


@limiter.limit("10 per minute")
@app.route("/register", methods=["GET", "POST"])
def register_student():
    # GET: redirect to homepage (signup form is on homepage)
    if request.method == "GET":
        return redirect("/")
    
    full_name = request.form.get(
        "full_name",
        request.form.get("name", "")
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

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

    # ---- Validation ----
    if not full_name:
        return render_template(
            "index.html",
            error="Student name is required."
        ), 400

    if len(full_name) > 120:
        return render_template(
            "index.html",
            error="Student name is too long."
        ), 400

    if not email or "@" not in email:
        return render_template(
            "index.html",
            error="A valid email is required."
        ), 400

    if len(password) < 6:
        return render_template(
            "index.html",
            error="Password must be at least 6 characters."
        ), 400

    # ---- Check duplicate email ----
    existing = service.get_student_by_email(email)
    if existing is not None:
        return render_template(
            "index.html",
            error="This email is already registered. Please log in."
        ), 400

    # ---- Create student ----
    password_hash = generate_password_hash(password)

    try:
        student_id = service.register_student(
            full_name=full_name,
            email=email,
            password_hash=password_hash
        )
    except ValueError as exc:
        return render_template(
            "index.html",
            error=str(exc)
        ), 400

    # ---- Log the student in ----
    session["student_id"] = student_id
    session["student_name"] = full_name
    session["student_age"] = age
    session["student_subject"] = subject
    session["student_level"] = level

    app.logger.info(
        "New student registered: %s (id=%s)", email, student_id
    )

    return redirect(
        url_for(
            "assessment",
            student_id=student_id
        )
    )


@limiter.limit("30 per minute")
@app.route("/login", methods=["GET"])
def login_page():
    """Show the login form."""
    if current_student_id() is not None:
        return redirect(
            url_for("assessment", student_id=current_student_id())
        )
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_submit():
    """Process the login form."""
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template(
            "login.html",
            error="Email and password are required."
        ), 400

    student = service.get_student_by_email(email)

    if student is None:
        return render_template(
            "login.html",
            error="Invalid email or password."
        ), 401

    if not student.get("password_hash"):
        return render_template(
            "login.html",
            error="This account has no password set."
        ), 401

    if not check_password_hash(student["password_hash"], password):
        return render_template(
            "login.html",
            error="Invalid email or password."
        ), 401

    # Success
    session["student_id"] = student["student_id"]
    session["student_name"] = student["full_name"]

    app.logger.info(
        "Student logged in: %s (id=%s)",
        email, student["student_id"]
    )

    return redirect(
        url_for("assessment", student_id=student["student_id"])
    )


@app.route("/logout", methods=["POST", "GET"])
def logout():
    """Log the student out and clear the session."""
    session.clear()
    return redirect(url_for("index"))


# ============================================================
# PASSWORD RESET
# ============================================================

RESET_TOKEN_TTL_MINUTES = 60


@limiter.limit("10 per minute")
@app.route("/forgot-password", methods=["GET"])
def forgot_password_page():
    """Show the 'forgot password' form."""
    return render_template("forgot_password.html")


@app.route("/forgot-password", methods=["POST"])
def forgot_password_submit():
    """Generate a reset token and (for now) show the reset link."""
    email = request.form.get("email", "").strip().lower()

    if not email:
        return render_template(
            "forgot_password.html",
            error="Please enter your email address."
        ), 400

    student = service.get_student_by_email(email)

    # Always show the same message (avoid user enumeration)
    generic_message = (
        "If an account with that email exists, "
        "a password reset link has been generated."
    )

    reset_link = None

    if student is not None:
        token = secrets.token_urlsafe(32)
        expires_at = (
            datetime.utcnow() + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
        ).isoformat()

        service.set_password_reset_token(
            email=email,
            token=token,
            expires_at=expires_at,
        )

        reset_link = url_for(
            "reset_password_page",
            token=token,
            _external=True,
        )

        app.logger.info(
            "Password reset requested for %s — token issued", email
        )

    return render_template(
        "forgot_password.html",
        message=generic_message,
        reset_link=reset_link,
        dev_mode=True,
    )


@limiter.limit("5 per minute")
@app.route("/reset-password/<token>", methods=["GET"])
def reset_password_page(token):
    """Show the reset password form."""
    if not token:
        return redirect(url_for("login_page"))

    student = service.get_student_by_reset_token(token)

    if student is None:
        return render_template(
            "reset_password.html",
            error="Invalid or missing reset token.",
            token=None,
        ), 400

    # Check expiry
    expires = student.get("password_reset_expires")
    if expires:
        try:
            expires_dt = datetime.fromisoformat(str(expires))
            if datetime.utcnow() > expires_dt:
                return render_template(
                    "reset_password.html",
                    error="This reset link has expired. Please request a new one.",
                    token=None,
                ), 400
        except Exception:
            pass

    return render_template(
        "reset_password.html",
        token=token,
    )


@app.route("/reset-password/<token>", methods=["POST"])
def reset_password_submit(token):
    """Process the reset password form."""
    if not token:
        return redirect(url_for("login_page"))

    student = service.get_student_by_reset_token(token)

    if student is None:
        return render_template(
            "reset_password.html",
            error="Invalid or missing reset token.",
            token=None,
        ), 400

    # Check expiry
    expires = student.get("password_reset_expires")
    if expires:
        try:
            expires_dt = datetime.fromisoformat(str(expires))
            if datetime.utcnow() > expires_dt:
                return render_template(
                    "reset_password.html",
                    error="This reset link has expired. Please request a new one.",
                    token=None,
                ), 400
        except Exception:
            pass

    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    if len(password) < 6:
        return render_template(
            "reset_password.html",
            error="Password must be at least 6 characters.",
            token=token,
        ), 400

    if password != password_confirm:
        return render_template(
            "reset_password.html",
            error="Passwords do not match.",
            token=token,
        ), 400

    new_hash = generate_password_hash(password)

    service.update_password(
        student_id=student["student_id"],
        password_hash=new_hash,
    )

    app.logger.info(
        "Password reset successfully for %s",
        student.get("email"),
    )

    return render_template(
        "reset_password.html",
        success=True,
        token=None,
    )


def reset_shuffle_for_assessment(assessment_id):
    """Remove stored shuffle order/seed for a given assessment."""
    key = str(assessment_id)

    store = session.get(SESSION_QUESTION_ORDER_KEY, {})
    if key in store:
        store.pop(key, None)
        session[SESSION_QUESTION_ORDER_KEY] = store

    seeds = session.get(SESSION_SHUFFLE_SEED_KEY, {})
    if key in seeds:
        seeds.pop(key, None)
        session[SESSION_SHUFFLE_SEED_KEY] = seeds

    session.modified = True


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

    try:
        from .database import assessment_exists
    except ImportError:
        from database import assessment_exists

    assessment_id = session.get(
        "assessment_id"
    )

    assessment_student_id = session.get(
        "assessment_student_id"
    )

    session_valid = (
        assessment_id is not None
        and assessment_student_id == student_id
        and assessment_exists(assessment_id)
    )

    if not session_valid:
        assessment_id = service.start_assessment(
            student_id=student_id,
            assessment_type="Diagnostic"
        )

        session["assessment_id"] = assessment_id
        session["assessment_student_id"] = student_id

        # Clear stale shuffle state so a NEW assessment always
        # starts with a fresh random order.
        session.pop(SESSION_QUESTION_ORDER_KEY, None)
        session.pop(SESSION_SHUFFLE_SEED_KEY, None)
        session.modified = True

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

        # Build a practice session ID (for shuffle key)
        practice_session_key = (
            f"practice_session_{student_id}_{concept_id}"
        )

        if practice_session_key not in session:
            import secrets
            session[practice_session_key] = secrets.token_hex(8)
            session.modified = True

        practice_session_id = session[practice_session_key]

        # Apply option shuffling to each question
        shuffled_questions = []
        for _, q_row in practice_questions.iterrows():
            q_dict = q_row.to_dict()
            q_dict = prepare_question_for_display(
                question=q_dict,
                assessment_id=f"practice_{practice_session_id}"
            )
            shuffled_questions.append(q_dict)

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
            questions=shuffled_questions
        )

    try:
        from .database import save_practice_attempt
    except ImportError:
        from database import save_practice_attempt

    # Retrieve the practice session ID (same one used at display time)
    practice_session_key = (
        f"practice_session_{student_id}_{concept_id}"
    )

    if practice_session_key not in session:
        import secrets
        session[practice_session_key] = secrets.token_hex(8)
        session.modified = True

    practice_session_id = session[practice_session_key]

    # Build a results list with the ORIGINAL question info
    results = []

    for _, question in practice_questions.iterrows():

        question_id = str(
            question["question_id"]
        )

        # The student submitted a DISPLAYED letter.
        # We must map it back to the ORIGINAL letter before scoring.
        displayed_answer = request.form.get(
            f"answer_{question_id}",
            ""
        ).strip().upper()

        # Get the same option mapping that was used at display time
        option_mapping = get_remembered_option_mapping(
            assessment_id=f"practice_{practice_session_id}",
            question_id=question_id
        )

        # displayed -> original
        original_answer = option_mapping.get(displayed_answer, "")

        correct_answer = str(
            question["correct_answer"]
        ).strip().upper()

        is_correct = (
            original_answer == correct_answer
            and bool(original_answer)
        )

        score = (
            100.0
            if is_correct
            else 0.0
        )

        save_practice_attempt(
            student_id=student_id,
            question_id=question_id,
            student_answer=original_answer,
            is_correct=is_correct,
            score=score
        )

        results.append(
            {
                "question_id": question_id,
                "is_correct": is_correct,
                "score": score,
                "student_answer": displayed_answer
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

    # Rebuild shuffled questions for display
    shuffled_questions = []
    for _, q_row in practice_questions.iterrows():
        q_dict = q_row.to_dict()
        q_dict = prepare_question_for_display(
            question=q_dict,
            assessment_id=f"practice_{practice_session_id}"
        )
        shuffled_questions.append(q_dict)

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
        questions=shuffled_questions,
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
@login_required
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
    "/report/<int:student_id>",
    methods=["GET"]
)
@login_required
def download_report(student_id):
    """Generate and download a PDF report for a student."""
    from flask import send_file
    from io import BytesIO

    # Authorization: only the logged-in student can download their own report
    if current_student_id() != student_id:
        return "Unauthorized", 403

    try:
        dashboard_data = get_student_dashboard_data(student_id)
    except ValueError as exc:
        return str(exc), 404
    except Exception:
        app.logger.exception(
            "PDF report failed for student_id=%s", student_id
        )
        return "Unable to generate the report.", 500

    student = dashboard_data.get("student")
    diagnosis = dashboard_data.get("diagnosis", [])
    priority = dashboard_data.get("learning_priorities", [])
    learning_path = dashboard_data.get("learning_path", [])
    overall_mastery = dashboard_data.get("overall_mastery")
    reassessments = dashboard_data.get("reassessments", [])

    try:
        pdf_bytes = generate_student_report(
            student=student,
            diagnosis=diagnosis,
            priority=priority,
            learning_path=learning_path,
            overall_mastery=overall_mastery,
            reassessments=reassessments,
        )
    except Exception:
        app.logger.exception(
            "PDF generation failed for student_id=%s", student_id
        )
        return "Unable to generate the report.", 500

    student_name = (student or {}).get("full_name", "student")
    safe_name = "".join(
        c if c.isalnum() else "_" for c in student_name
    ).strip("_") or "student"

    filename = f"smart_knowledge_report_{safe_name}_{student_id}.pdf"

    app.logger.info(
        "PDF report generated for student_id=%s (%s bytes)",
        student_id, len(pdf_bytes)
    )

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@app.route(
    "/teacher-dashboard",
    methods=["GET"]
)
def teacher_dashboard():
    # Read filters from query params
    subject_filter = request.args.get("subject", "").strip() or None
    level_filter = request.args.get("level", "").strip() or None
    status_filter = request.args.get("status", "").strip() or None

    try:
        dashboard_data = get_teacher_dashboard_data(
            subject_filter=subject_filter,
            level_filter=level_filter,
            status_filter=status_filter
        )
    except Exception:
        app.logger.exception(
            "Teacher dashboard failed."
        )
        return (
            "Unable to load the teacher dashboard.",
            500
        )

    # Pass current filter values to the template
    dashboard_data["current_filters"] = {
        "subject": subject_filter or "",
        "level": level_filter or "",
        "status": status_filter or "",
    }

    return render_template(
        "teacher_dashboard.html",
        **dashboard_data
    )



@app.route(
    "/assessment/<int:student_id>/submit",
    methods=["POST"]
)
def submit_answer(student_id):
    try:
        from .database import assessment_exists
    except ImportError:
        from database import assessment_exists

    reassessment_id = session.get(
        "reassessment_id"
    )
    reassessment_student_id = session.get(
        "reassessment_student_id"
    )

    if (
        reassessment_id is not None
        and reassessment_student_id == student_id
        and assessment_exists(reassessment_id)
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
            or not assessment_exists(assessment_id)
        ):
            return (
                "Assessment session is invalid. "
                "Please restart the assessment.",
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
# ML ROUTES
# ============================================================

@app.route("/ml/insights/<int:student_id>", methods=["GET"])
@login_required
def ml_insights(student_id):
    """Show ML-driven insights for a student."""
    if current_student_id() != student_id:
        return "Unauthorized", 403

    try:
        dashboard_data = get_student_dashboard_data(student_id)
    except ValueError as exc:
        return str(exc), 404
    except Exception:
        app.logger.exception(
            "ML insights failed for student_id=%s", student_id
        )
        return "Unable to load ML insights.", 500

    student = dashboard_data.get("student", {})
    diagnosis = dashboard_data.get("diagnosis", [])

    # ---- Compute student-level features for clustering ----
    import statistics
    masteries = [
        float(item.get("mastery", 0)) for item in diagnosis
    ] or [0.0]

    cluster_features = {
        "avg_mastery": sum(masteries) / len(masteries),
        "std_mastery": (
            statistics.pstdev(masteries) if len(masteries) > 1 else 0.0
        ),
        "avg_response_time": 45.0,
        "total_practice": int(
            (dashboard_data.get("practice_summary") or {}).get("total_attempts", 0)
        ),
        "reassessment_rate": 0.5,
        "avg_improvement": 0.0,
        "avg_accuracy": float(
            (dashboard_data.get("practice_summary") or {}).get("accuracy", 0) or 0
        ),
        "n_concepts": len(diagnosis),
    }

    cluster_result = predict_student_cluster(cluster_features)

    # ---- Per-concept risk predictions ----
    risk_predictions = []
    for item in diagnosis:
        try:
            features = {
                "subject_id": 1,
                "difficulty_encoded": 1,
                "practice_sessions": cluster_features["total_practice"] // max(len(diagnosis), 1),
                "avg_response_time": 45.0,
                "reassessment_flag": 1,
                "improvement": 0.0,
                "questions_correct": round(
                    float(item.get("mastery", 0)) / 100.0 * 6
                ),
            }
            risk = predict_student_risk(features)
            if risk:
                risk_predictions.append({
                    "concept_name": item.get("concept_name", ""),
                    "mastery": float(item.get("mastery", 0)),
                    **risk,
                })
        except Exception:
            continue

    # ---- Recommendations ----
    mastery_map = {
        int(item["concept_id"]): float(item.get("mastery", 0))
        for item in diagnosis
        if "concept_id" in item
    }

    try:
        concepts_df = load_concepts()
        recommendations = recommend_concepts(
            student_id=student_id,
            student_mastery=mastery_map,
            concepts_df=concepts_df,
            top_k=5,
        )
        # Log for debugging
        if recommendations:
            app.logger.info(
                "Generated %d recommendations for student %s",
                len(recommendations), student_id
            )
        else:
            app.logger.warning(
                "No recommendations generated for student %s", student_id
            )
    except Exception as exc:
        app.logger.exception(
            "Recommendation failed for student %s: %s",
            student_id, exc
        )
        recommendations = []

    metrics = get_model_metrics()

    # ---- SHAP Explanation (Explainable AI) ----
    explanation = None
    explanation_text = ""

    if risk_predictions:
        # Use the highest-risk concept for SHAP explanation
        highest_risk = max(
            risk_predictions,
            key=lambda x: x.get("risk_probability", 0),
        )

        # Build the same feature vector used for prediction
        explain_features = {
            "subject_id": 1,
            "difficulty_encoded": 1,
            "practice_sessions": cluster_features["total_practice"] // max(len(diagnosis), 1),
            "avg_response_time": 45.0,
            "reassessment_flag": 1,
            "improvement": 0.0,
            "questions_correct": round(
                highest_risk.get("mastery", 0) / 100.0 * 6
            ),
        }

        try:
            explanation = explain_risk(explain_features)
            if explanation and "error" not in explanation:
                explanation_text = explanation.get("text_summary", "")
                explanation["concept_name"] = highest_risk.get("concept_name", "")
        except Exception:
            app.logger.exception("SHAP explanation failed")
            explanation = None

    # ---- RL Adaptive Path ----
    adaptive_path = []
    try:
        adaptive_path = plan_adaptive_path(
            student_mastery_dict=mastery_map,
            n_steps=8,
            concepts_df=concepts_df,
        )
        app.logger.info(
            "RL adaptive path generated: %d concepts for student %s",
            len(adaptive_path), student_id
        )
    except Exception as exc:
        app.logger.exception(
            "RL path planning failed for student %s: %s",
            student_id, exc
        )
        adaptive_path = []

    return render_template(
        "ml_insights.html",
        student=student,
        student_id=student_id,
        cluster=cluster_result,
        risk_predictions=risk_predictions,
        recommendations=recommendations,
        metrics=metrics,
        models_available=models_available(),
        explanation=explanation,
        explanation_text=explanation_text,
        adaptive_path=adaptive_path,
    )


@app.route("/ml/metrics", methods=["GET"])
def ml_metrics_page():
    """Public page showing all ML model metrics."""
    metrics = get_model_metrics()
    return render_template(
        "ml_metrics.html",
        metrics=metrics,
        models_available=models_available(),
    )



# ============================================================
# AI ASSISTANT (LLM + RAG)
# ============================================================

@app.route("/chat", methods=["GET"])
@login_required
def chat_page():
    """Show the AI assistant chat page."""
    student_id = current_student_id()

    return render_template(
        "chat.html",
        student_id=student_id,
        llm_available=llm_is_available(),
    )


@limiter.limit("15 per minute")
@app.route("/chat/ask", methods=["POST"])
@login_required
def chat_ask():
    """Process a chat message and return the AI answer."""
    from flask import jsonify

    if not llm_is_available():
        return jsonify({
            "error": "AI assistant is not configured. Please set GROQ_API_KEY."
        }), 503

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Message is required."}), 400

    if len(message) > 1000:
        return jsonify({"error": "Message is too long."}), 400

    history = data.get("history", [])
    if not isinstance(history, list):
        history = []

    subject_name = session.get("student_subject", "")
    level = session.get("student_level", "")

    try:
        result = llm_chat(
            message=message,
            conversation_history=history,
            subject_name=subject_name,
            level=level,
            top_k=5,
        )
    except Exception:
        app.logger.exception("Chat request failed")
        return jsonify({"error": "AI assistant is temporarily unavailable."}), 500

    if result.get("error"):
        return jsonify({"error": result["error"]}), 500

    sources = []
    for src in result.get("sources", [])[:3]:
        meta = src.get("metadata", {})
        sources.append({
            "type": meta.get("type", "content"),
            "concept": meta.get("concept_name", ""),
            "text": src.get("text", "")[:200],
        })

    return jsonify({
        "answer": result.get("answer", ""),
        "sources": sources,
    })



# ============================================================
# FEYNMAN BOARD
# ============================================================

@app.route("/feynman/<int:student_id>/<int:concept_id>", methods=["GET"])
@login_required
def feynman_page(student_id, concept_id):
    """Show the Feynman board for a concept."""
    if current_student_id() != student_id:
        return "Unauthorized", 403

    try:
        from .database import get_feynman_attempts
    except ImportError:
        from database import get_feynman_attempts

    # Get concept metadata
    try:
        content = get_learning_content_for_concept(concept_id)
    except Exception:
        content = None

    if content is None:
        return "Concept not found.", 404

    # Get previous attempts
    try:
        previous_attempts = get_feynman_attempts(
            student_id=student_id,
            concept_id=concept_id,
            limit=10,
        )
    except Exception:
        previous_attempts = []

    return render_template(
        "feynman.html",
        student_id=student_id,
        concept_id=concept_id,
        concept_name=content.get("concept_name", ""),
        learning_objective=content.get("learning_objective", ""),
        llm_available=llm_is_available(),
        previous_attempts=previous_attempts,
        result=None,
        explanation="",
    )


@app.route("/feynman/<int:student_id>/<int:concept_id>", methods=["POST"])
@login_required
def feynman_submit(student_id, concept_id):
    """Process a Feynman explanation submission."""
    if current_student_id() != student_id:
        return "Unauthorized", 403

    explanation = request.form.get("explanation", "").strip()

    if not explanation or len(explanation) < 20:
        return _render_feynman_page(
            student_id, concept_id,
            explanation=explanation,
            error="Please write at least a few sentences explaining the concept.",
        )

    if len(explanation) > 5000:
        return _render_feynman_page(
            student_id, concept_id,
            explanation=explanation,
            error="Explanation is too long (max 5000 characters).",
        )

    # Get concept metadata
    try:
        content = get_learning_content_for_concept(concept_id)
    except Exception:
        content = None

    if content is None:
        return "Concept not found.", 404

    # Evaluate the explanation
    evaluation = evaluate_feynman_explanation(
        concept_name=content.get("concept_name", ""),
        explanation=explanation,
        learning_objective=content.get("learning_objective", ""),
        key_points=content.get("key_points", ""),
        common_mistakes=content.get("common_mistakes", ""),
    )

    # Save the attempt
    try:
        from .database import save_feynman_attempt
    except ImportError:
        from database import save_feynman_attempt

    try:
        save_feynman_attempt(
            student_id=student_id,
            concept_id=concept_id,
            explanation=explanation,
            score=evaluation.get("score", 0),
            feedback=evaluation.get("feedback", ""),
            strengths=evaluation.get("strengths", ""),
            gaps=evaluation.get("gaps", ""),
            suggestions=evaluation.get("suggestions", ""),
        )
    except Exception:
        app.logger.exception("Failed to save Feynman attempt")

    app.logger.info(
        "Feynman attempt: student=%s concept=%s score=%.1f",
        student_id, concept_id, evaluation.get("score", 0)
    )

    return _render_feynman_page(
        student_id, concept_id,
        explanation=explanation,
        result=evaluation,
    )


def _render_feynman_page(student_id, concept_id, explanation="", result=None, error=None):
    """Helper: render the Feynman page with all required context."""
    try:
        from .database import get_feynman_attempts
    except ImportError:
        from database import get_feynman_attempts

    try:
        content = get_learning_content_for_concept(concept_id)
    except Exception:
        content = None

    if content is None:
        return "Concept not found.", 404

    try:
        previous_attempts = get_feynman_attempts(
            student_id=student_id,
            concept_id=concept_id,
            limit=10,
        )
    except Exception:
        previous_attempts = []

    return render_template(
        "feynman.html",
        student_id=student_id,
        concept_id=concept_id,
        concept_name=content.get("concept_name", ""),
        learning_objective=content.get("learning_objective", ""),
        llm_available=llm_is_available(),
        previous_attempts=previous_attempts,
        explanation=explanation,
        result=result,
        error=error,
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
