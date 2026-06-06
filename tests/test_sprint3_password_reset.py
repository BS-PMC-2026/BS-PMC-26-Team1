"""BP2T-159: Forgot/Reset Password Flow — unit tests."""

from datetime import datetime, timedelta

from werkzeug.security import check_password_hash

from app.models import PasswordResetToken, User, db
from app.services.security_service import (
    consume_password_reset_token,
    create_password_reset_token,
    mark_token_used,
    RESET_TOKEN_TTL_HOURS,
)


# -- positive --------------------------------------------------------------
def test_forgot_password_page_renders(client):
    response = client.get("/forgot-password")
    assert response.status_code == 200
    assert b"Forgot" in response.data or b"forgot" in response.data


def test_forgot_password_creates_token_for_known_user(client, student_user):
    response = client.post(
        "/forgot-password",
        data={"email": student_user.email},
        follow_redirects=False,
    )
    assert response.status_code == 302
    tokens = PasswordResetToken.query.filter_by(user_id=student_user.id).all()
    assert len(tokens) == 1
    assert tokens[0].used is False


def test_reset_password_updates_password_hash(client, student_user):
    token_row = create_password_reset_token(student_user)
    db.session.commit()
    response = client.post(
        f"/reset-password/{token_row.token}",
        data={"password": "NewPassw0rd!", "confirm_password": "NewPassw0rd!"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    refreshed = db.session.get(User, student_user.id)
    assert check_password_hash(refreshed.password_hash, "NewPassw0rd!")


# -- negative --------------------------------------------------------------
def test_forgot_password_returns_neutral_message_for_unknown_email(client):
    """Anti-enumeration: don't reveal whether the email is registered."""
    response = client.post(
        "/forgot-password",
        data={"email": "ghost@nowhere.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    # neutral message regardless of whether user exists
    assert PasswordResetToken.query.count() == 0


def test_reset_with_invalid_token_redirects(client):
    response = client.get("/reset-password/invalid-token-xyz", follow_redirects=False)
    assert response.status_code == 302
    assert "/forgot-password" in response.headers["Location"]


def test_reset_with_mismatched_passwords_does_not_update(client, student_user):
    token_row = create_password_reset_token(student_user)
    db.session.commit()
    old_hash = student_user.password_hash
    client.post(
        f"/reset-password/{token_row.token}",
        data={"password": "abc12345", "confirm_password": "different"},
        follow_redirects=False,
    )
    refreshed = db.session.get(User, student_user.id)
    assert refreshed.password_hash == old_hash


# -- edge ------------------------------------------------------------------
def test_used_token_cannot_be_reused(app, student_user):
    token_row = create_password_reset_token(student_user)
    db.session.commit()
    mark_token_used(token_row)
    db.session.commit()
    assert consume_password_reset_token(token_row.token) is None


def test_expired_token_is_rejected(app, student_user):
    token_row = create_password_reset_token(student_user)
    token_row.expires_at = datetime.utcnow() - timedelta(hours=1)
    db.session.commit()
    assert consume_password_reset_token(token_row.token) is None


def test_token_ttl_is_one_hour(app, student_user):
    token_row = create_password_reset_token(student_user)
    db.session.commit()
    delta = token_row.expires_at - token_row.created_at
    # within a few seconds of 1 hour
    assert abs(delta.total_seconds() - RESET_TOKEN_TTL_HOURS * 3600) < 5
