"""
Main app factory — used for both standalone (4_saaed only) and the
full combined project (all four folders merged together).

Standalone mode  : only intro_bp loads; stub routes fill the gaps.
Combined mode    : all blueprints are discovered automatically via
                   try/except imports — no manual changes needed when
                   team members add their files to the project.

Run from the 4_saaed/ folder (standalone):
    python app.py

Run from the combined ANTE/ folder:
    python app.py
"""

import importlib
import os

from flask import Flask, session, redirect
from app.models import db


def _try_register(app, module_path, blueprint_name):
    """Import a blueprint and register it. Returns True on success."""
    try:
        module = importlib.import_module(module_path)
        bp = getattr(module, blueprint_name)
        app.register_blueprint(bp)
        return True
    except (ImportError, AttributeError):
        return False


def create_app(test_config=None):
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project_v2.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = os.environ.get(
        "SECRET_KEY",
        "default-secret-key-for-dev"
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    # --- Core blueprint (always present in this folder) ---
    from app.routes.intro import intro_bp
    app.register_blueprint(intro_bp)

    # --- Optional blueprints from other team members ---
    # These load automatically once the full project is assembled.
    has_main = _try_register(app, "app.routes.main", "main_bp")
    has_auth = _try_register(app, "app.routes.auth", "auth_bp")
    has_pipeline = _try_register(app, "app.routes.pipeline", "pipeline_bp")
    has_exercise = _try_register(app, "app.routes.exercise", "exercise_bp")
    has_progress = _try_register(app, "app.routes.progress", "progress_bp")
    has_lecturer = _try_register(app, "app.routes.lecturer", "lecturer_bp")

    # --- Standalone stubs (only active when running 4_saaed alone) ---
    if not has_main:
        @app.route("/")
        def home():
            return redirect("/intro")

    if not has_auth:
        # Auto-login so protected routes do not crash in standalone mode.
        @app.before_request
        def auto_login():
            if not session.get("user_id"):
                from app.models import User

                test_user = User.query.filter_by(
                    email="test@example.com"
                ).first()

                if test_user:
                    session["user_id"] = test_user.id
                    session["user_name"] = test_user.full_name
                    session["role"] = test_user.role

        @app.route("/logout")
        def logout():
            session.clear()
            return redirect("/")

    if not has_pipeline:
        @app.route("/pipeline")
        def pipeline_stub():
            return redirect("/intro")

    if not has_exercise:
        @app.route("/exercise")
        def exercise_stub():
            return redirect("/intro")

    if not has_progress:
        @app.route("/progress")
        def progress_stub():
            return redirect("/intro")

    if not has_lecturer:
        @app.route("/lecturer")
        def lecturer_stub():
            return redirect("/intro")

        @app.route("/lecturer/dashboard")
        def lecturer_dashboard_stub():
            return redirect("/intro")

        @app.route("/lecturer/questions")
        def lecturer_questions_stub():
            return redirect("/intro")

        @app.route("/lecturer/questions/create", methods=["GET", "POST"])
        def lecturer_question_create_stub():
            return redirect("/intro")

        @app.route("/lecturer/questions/<int:question_id>/edit", methods=["GET", "POST"])
        def lecturer_question_edit_stub(question_id):
            return redirect("/intro")

        @app.route("/lecturer/questions/<int:question_id>/delete", methods=["POST"])
        def lecturer_question_delete_stub(question_id):
            return redirect("/intro")

    with app.app_context():
        db.create_all()
        _seed_test_user()

    return app


def _seed_test_user():
    """Create a default test user so standalone mode works out of the box."""
    from app.models import User
    from werkzeug.security import generate_password_hash

    if not User.query.filter_by(email="test@example.com").first():
        test_user = User(
            full_name="Test Student",
            email="test@example.com",
            password_hash=generate_password_hash("password123"),
            role="student",
        )
        db.session.add(test_user)
        db.session.commit()
