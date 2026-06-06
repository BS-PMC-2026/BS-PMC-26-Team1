import logging
import os
import urllib.parse
from datetime import datetime, timedelta

from flask import Flask, redirect, render_template, request, session, url_for

from app.models import db


SESSION_TIMEOUT_MINUTES = 60


def _is_safe_internal_path(path: str) -> bool:
    return path.startswith("/static/") or path == "/favicon.ico"


def _ensure_login_freshness(app: Flask):
    @app.before_request
    def _check_session_timeout():
        user_id = session.get("user_id")
        if not user_id:
            return None
        login_iso = session.get("login_at")
        if not login_iso:
            session["login_at"] = datetime.utcnow().isoformat()
            return None
        try:
            login_at = datetime.fromisoformat(login_iso)
        except (TypeError, ValueError):
            session["login_at"] = datetime.utcnow().isoformat()
            return None
        if datetime.utcnow() - login_at > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            session.clear()
            if request.method == "GET" and not _is_safe_internal_path(request.path):
                from flask import flash

                flash("Your session expired. Please log in again.", "warning")
                return redirect(url_for("auth.login"))
        return None


def _ensure_maintenance_gate(app: Flask):
    @app.before_request
    def _maintenance_gate():
        if request.endpoint is None:
            return None
        if _is_safe_internal_path(request.path):
            return None
        allowed_endpoints = {
            "auth.login",
            "auth.logout",
            "auth.forgot_password",
            "auth.reset_password",
            "static",
        }
        try:
            from app.services.settings_service import is_maintenance_mode
        except Exception:
            return None
        try:
            in_maintenance = is_maintenance_mode()
        except Exception:
            in_maintenance = False
        if not in_maintenance:
            return None
        if session.get("role") == "admin":
            return None
        if request.endpoint in allowed_endpoints:
            return None
        if request.endpoint and request.endpoint.startswith("admin."):
            return None
        return render_template("maintenance.html"), 503


def _ensure_csrf(app: Flask):
    @app.context_processor
    def _inject_csrf():
        from app.services.security_service import get_or_create_csrf_token

        try:
            token = get_or_create_csrf_token()
        except Exception:
            token = ""
        return {"csrf_token": token}


def _ensure_settings_context(app: Flask):
    @app.context_processor
    def _inject_settings():
        try:
            from app.services.settings_service import get_setting, is_maintenance_mode

            return {
                "system_name": get_setting("system_name", "ANTE CI/CD Academy"),
                "maintenance_mode_on": is_maintenance_mode(),
            }
        except Exception:
            return {"system_name": "ANTE CI/CD Academy", "maintenance_mode_on": False}


def _register_error_handlers(app: Flask):
    @app.errorhandler(404)
    def _not_found(_err):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def _server_error(_err):
        try:
            db.session.rollback()
        except Exception:
            pass
        app.logger.exception("Unhandled server error")
        return render_template("500.html"), 500


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project_v2.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = os.environ.get("SECRET_KEY", "default-secret-key-for-dev")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    use_sqlserver = os.environ.get("USE_SQLSERVER", "0") == "1"
    if use_sqlserver:
        sqlserver_conn = (
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=(localdb)\\MSSQLLocalDB;"
            "Database=ANTE_ACADEMIC;"
            "Trusted_Connection=yes;"
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(sqlserver_conn)
        )

    if os.environ.get("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.certificate import certificate_bp
    from app.routes.exercise import exercise_bp
    from app.routes.intro import intro_bp
    from app.routes.lecturer import lecturer_bp
    from app.routes.main import main_bp
    from app.routes.pipeline import pipeline_bp
    from app.routes.progress import progress_bp

    app.register_blueprint(intro_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pipeline_bp)
    app.register_blueprint(exercise_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(lecturer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(certificate_bp)

    _ensure_login_freshness(app)
    _ensure_maintenance_gate(app)
    _ensure_csrf(app)
    _ensure_settings_context(app)
    _register_error_handlers(app)

    if not app.config.get("TESTING"):
        app.logger.setLevel(logging.INFO)

    with app.app_context():
        db.create_all()
        from app.seed import bootstrap_database
        from app.services.db_init import ensure_schema_compatibility

        ensure_schema_compatibility()
        bootstrap_database()

    return app
