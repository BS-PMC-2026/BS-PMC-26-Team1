from __future__ import annotations

import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from flask import current_app, has_request_context, request, session

from app.models import LoginAttempt, PasswordResetToken, User, db
from app.services.settings_service import get_setting_int

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
SESSION_TIMEOUT_MINUTES = 60
RESET_TOKEN_TTL_HOURS = 1


def _request_ip() -> Optional[str]:
    if not has_request_context():
        return None
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def record_login_attempt(email: str, success: bool) -> LoginAttempt:
    attempt = LoginAttempt(
        email=(email or "").strip().lower(),
        success=success,
        ip_address=_request_ip(),
    )
    db.session.add(attempt)
    db.session.flush()
    return attempt


def is_account_locked(email: str) -> Tuple[bool, Optional[datetime]]:
    if not email:
        return False, None
    norm = email.strip().lower()
    window_start = datetime.utcnow() - timedelta(minutes=LOCKOUT_MINUTES)
    last_success = (
        LoginAttempt.query.filter(
            LoginAttempt.email == norm,
            LoginAttempt.success.is_(True),
            LoginAttempt.attempted_at >= window_start,
        )
        .order_by(LoginAttempt.attempted_at.desc())
        .first()
    )
    if last_success:
        return False, None

    failures = (
        LoginAttempt.query.filter(
            LoginAttempt.email == norm,
            LoginAttempt.success.is_(False),
            LoginAttempt.attempted_at >= window_start,
        )
        .order_by(LoginAttempt.attempted_at.desc())
        .all()
    )
    if len(failures) >= MAX_FAILED_ATTEMPTS:
        unlock_at = failures[0].attempted_at + timedelta(minutes=LOCKOUT_MINUTES)
        if unlock_at > datetime.utcnow():
            return True, unlock_at
    return False, None


def create_password_reset_token(user: User) -> PasswordResetToken:
    raw_token = secrets.token_urlsafe(32)
    token_row = PasswordResetToken(
        token=raw_token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(hours=RESET_TOKEN_TTL_HOURS),
        used=False,
    )
    db.session.add(token_row)
    db.session.flush()
    return token_row


def consume_password_reset_token(token: str) -> Optional[PasswordResetToken]:
    if not token:
        return None
    row = db.session.get(PasswordResetToken, token)
    if not row:
        return None
    if row.used:
        return None
    if row.expires_at < datetime.utcnow():
        return None
    return row


def mark_token_used(row: PasswordResetToken) -> None:
    row.used = True


def get_or_create_csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(24)
        session["_csrf_token"] = token
        session.modified = True
    return token


def validate_csrf_token(submitted: Optional[str]) -> bool:
    try:
        if not current_app.config.get("CSRF_ENABLED", True):
            return True
    except RuntimeError:
        pass
    expected = session.get("_csrf_token")
    if not expected or not submitted:
        return False
    return hmac.compare_digest(str(expected), str(submitted))


def validate_password(password: str) -> Optional[str]:
    min_len = get_setting_int("min_password_length", 8)
    if not password or len(password) < min_len:
        return f"Password must be at least {min_len} characters long."
    if len(password) > 128:
        return "Password is too long (maximum 128 characters)."
    return None


def validate_text_field(value: Optional[str], field_name: str, *, min_len: int = 1, max_len: int = 200, required: bool = True) -> Optional[str]:
    raw = (value or "").strip()
    if required and not raw:
        return f"{field_name} is required."
    if raw and len(raw) < min_len:
        return f"{field_name} must be at least {min_len} characters."
    if len(raw) > max_len:
        return f"{field_name} must be at most {max_len} characters."
    return None


def validate_email(email: Optional[str]) -> Optional[str]:
    if not email or "@" not in email:
        return "A valid email address is required."
    if len(email) > 254:
        return "Email address is too long."
    local, _, domain = email.partition("@")
    if not local or not domain or "." not in domain:
        return "A valid email address is required."
    return None
