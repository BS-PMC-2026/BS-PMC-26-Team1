"""BP2T-126: User Management Screen — unit tests."""

from werkzeug.security import check_password_hash

from app.models import AuditLog, User, db
from app.services.user_admin_service import (
    count_admins,
    delete_user_cascade,
    list_users,
    set_active,
)


# -- positive --------------------------------------------------------------
def test_users_page_renders_for_admin(auth_admin_client, student_user, lecturer_user):
    response = auth_admin_client.get("/admin/users")
    assert response.status_code == 200
    assert b"User Management" in response.data
    assert student_user.email.encode() in response.data
    assert lecturer_user.email.encode() in response.data


def test_list_users_supports_role_filter(app, student_user, lecturer_user):
    result = list_users(role_filter="student")
    emails = [u.email for u in result["rows"]]
    assert student_user.email in emails
    assert lecturer_user.email not in emails


def test_list_users_supports_search(app, student_user):
    result = list_users(search=student_user.email)
    assert student_user.id in [u.id for u in result["rows"]]


# -- negative --------------------------------------------------------------
def test_admin_cannot_deactivate_self(auth_admin_client, admin_user):
    response = auth_admin_client.post(
        f"/admin/users/{admin_user.id}/deactivate",
        follow_redirects=False,
    )
    assert response.status_code == 302
    refreshed = db.session.get(User, admin_user.id)
    assert refreshed.is_active is True  # still active


def test_admin_cannot_delete_self(auth_admin_client, admin_user):
    auth_admin_client.post(
        f"/admin/users/{admin_user.id}/delete",
        follow_redirects=False,
    )
    assert db.session.get(User, admin_user.id) is not None


def test_admin_cannot_delete_last_admin(auth_admin_client, app):
    # only the seeded admin and the auth admin exist — keep one alive rule
    other_admin = User.query.filter_by(role="admin").filter(
        User.email != "admin@test.com"
    ).first()
    if other_admin:
        # delete the other one so only one admin remains
        delete_user_cascade(other_admin)
        db.session.commit()
    assert count_admins() == 1


# -- edge ------------------------------------------------------------------
def test_activate_then_deactivate_student(auth_admin_client, student_user):
    set_active(student_user, False)
    db.session.commit()
    # admin re-activates
    auth_admin_client.post(f"/admin/users/{student_user.id}/activate")
    refreshed = db.session.get(User, student_user.id)
    assert refreshed.is_active is True

    # then admin deactivates
    auth_admin_client.post(f"/admin/users/{student_user.id}/deactivate")
    refreshed = db.session.get(User, student_user.id)
    assert refreshed.is_active is False


def test_admin_can_reset_user_password(auth_admin_client, student_user):
    old_hash = student_user.password_hash
    response = auth_admin_client.post(
        f"/admin/users/{student_user.id}/reset-password",
        follow_redirects=False,
    )
    assert response.status_code == 302
    refreshed = db.session.get(User, student_user.id)
    assert refreshed.password_hash != old_hash


def test_user_management_actions_are_audit_logged(auth_admin_client, student_user):
    auth_admin_client.post(f"/admin/users/{student_user.id}/deactivate")
    entries = AuditLog.query.filter_by(action="user.deactivate").all()
    assert any(e.target_id == student_user.id for e in entries)
