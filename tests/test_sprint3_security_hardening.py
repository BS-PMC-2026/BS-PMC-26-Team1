"""BP2T-174: Security Hardening & Edge Cases — unit tests."""

from datetime import datetime, timedelta

from app.models import LoginAttempt, db
from app.services.security_service import (
    LOCKOUT_MINUTES,
    MAX_FAILED_ATTEMPTS,
    is_account_locked,
    record_login_attempt,
    validate_email,
    validate_password,
    validate_text_field,
)


# -- positive --------------------------------------------------------------
def test_valid_password_passes(app):
    assert validate_password("longenough") is None


def test_valid_email_passes(app):
    assert validate_email("good@example.com") is None


def test_valid_text_field_passes(app):
    assert validate_text_field("hello", "Name") is None


def test_csrf_protection_enabled_in_csrf_client(csrf_client, student_user):
    response = csrf_client.post(
        "/login",
        data={"email": student_user.email, "password": "password123"},
        follow_redirects=False,
    )
    # CSRF blocks the request and redirects back to login
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# -- negative --------------------------------------------------------------
def test_short_password_is_rejected(app):
    assert validate_password("short") is not None


def test_invalid_email_is_rejected(app):
    assert validate_email("not-an-email") is not None


def test_empty_required_field_is_rejected(app):
    assert validate_text_field("", "Name") is not None


def test_oversized_text_field_is_rejected(app):
    too_long = "x" * 5000
    assert validate_text_field(too_long, "Name", max_len=200) is not None


# -- edge ------------------------------------------------------------------
def test_account_locks_after_five_failed_attempts(app, student_user):
    for _ in range(MAX_FAILED_ATTEMPTS):
        record_login_attempt(student_user.email, success=False)
    db.session.commit()
    locked, unlock_at = is_account_locked(student_user.email)
    assert locked is True
    assert unlock_at is not None
    assert unlock_at > datetime.utcnow()


def test_account_not_locked_after_fewer_than_max_failures(app, student_user):
    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        record_login_attempt(student_user.email, success=False)
    db.session.commit()
    locked, _ = is_account_locked(student_user.email)
    assert locked is False


def test_successful_login_after_failures_unlocks(app, student_user):
    for _ in range(MAX_FAILED_ATTEMPTS):
        record_login_attempt(student_user.email, success=False)
    record_login_attempt(student_user.email, success=True)
    db.session.commit()
    locked, _ = is_account_locked(student_user.email)
    assert locked is False


def test_lockout_window_is_15_minutes(app):
    assert LOCKOUT_MINUTES == 15
    assert MAX_FAILED_ATTEMPTS == 5


def test_500_handler_renders_friendly_page(app):
    """The custom 500 template renders without leaking stack traces."""
    # Force Flask to invoke the registered error handler instead of re-raising in test mode.
    app.config["PROPAGATE_EXCEPTIONS"] = False
    app.testing = False

    @app.route("/_force-error-internal-only")
    def _force_error():
        raise ValueError("intentional sentinel for test")

    client = app.test_client()
    response = client.get("/_force-error-internal-only")
    assert response.status_code == 500
    assert b"went wrong" in response.data.lower() or b"error" in response.data.lower()
    # stack trace not leaked
    assert b"ValueError" not in response.data
    assert b"Traceback" not in response.data
    # restore
    app.testing = True
    app.config["PROPAGATE_EXCEPTIONS"] = True
