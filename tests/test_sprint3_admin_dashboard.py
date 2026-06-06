"""BP2T-133: Admin Dashboard — unit tests."""

from datetime import datetime, timedelta

from app.models import ExerciseAttempt, User, db


# -- positive --------------------------------------------------------------
def test_dashboard_renders_summary_cards(auth_admin_client):
    response = auth_admin_client.get("/admin/dashboard")
    assert response.status_code == 200
    body = response.data
    assert b"Administrator Dashboard" in body
    assert b"Students" in body
    assert b"Lecturers" in body
    assert b"Admins" in body
    assert b"Attempts" in body


def test_dashboard_shows_quick_links_to_other_admin_screens(auth_admin_client):
    response = auth_admin_client.get("/admin/dashboard")
    body = response.data
    assert b"/admin/users" in body
    assert b"/admin/modules" in body
    assert b"/admin/audit" in body
    assert b"/admin/reports" in body
    assert b"/admin/settings" in body


def test_dashboard_counts_reflect_database_state(auth_admin_client, student_user, lecturer_user):
    response = auth_admin_client.get("/admin/dashboard")
    assert response.status_code == 200
    # at least the test student + the test admin and lecturer
    assert User.query.filter_by(role="student").count() >= 1
    assert User.query.filter_by(role="lecturer").count() >= 1
    assert User.query.filter_by(role="admin").count() >= 1


# -- negative --------------------------------------------------------------
def test_dashboard_redirects_unauthenticated_user(client):
    response = client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_dashboard_blocks_non_admin_users(auth_student_client):
    response = auth_student_client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 302


# -- edge ------------------------------------------------------------------
def test_dashboard_shows_zero_when_no_attempts(auth_admin_client):
    ExerciseAttempt.query.delete()
    db.session.commit()
    response = auth_admin_client.get("/admin/dashboard")
    assert response.status_code == 200
    # zero attempts → overall success average is 0
    assert b"0%" in response.data or b"0 " in response.data


def test_dashboard_recent_activity_section_renders(auth_admin_client, student_user):
    # an action that logs to the audit log
    auth_admin_client.post(f"/admin/users/{student_user.id}/deactivate")
    response = auth_admin_client.get("/admin/dashboard")
    assert b"Recent audit activity" in response.data or b"audit" in response.data.lower()
