"""BP2T-151: End-to-End Audit Log System — unit tests."""

import json

from app.models import AuditLog, db
from app.services.audit_service import list_audit_logs, log_action, recent_actions


# -- positive --------------------------------------------------------------
def test_log_action_creates_audit_row(app):
    entry = log_action("test.action", target_type="thing", target_id=1, details={"k": "v"})
    db.session.commit()
    assert entry.id is not None
    assert entry.action == "test.action"
    assert entry.target_id == 1
    assert entry.details == {"k": "v"}


def test_audit_page_renders_for_admin(auth_admin_client):
    response = auth_admin_client.get("/admin/audit")
    assert response.status_code == 200
    assert b"Audit Log" in response.data


def test_audit_filter_by_action_works(app):
    log_action("alpha.event", commit=True)
    log_action("beta.event", commit=True)
    result = list_audit_logs(action_filter="alpha")
    actions = [e.action for e in result["rows"]]
    assert "alpha.event" in actions
    assert "beta.event" not in actions


# -- negative --------------------------------------------------------------
def test_audit_page_blocks_non_admin(auth_student_client):
    response = auth_student_client.get("/admin/audit", follow_redirects=False)
    assert response.status_code == 302


def test_audit_filter_with_no_matches_returns_empty(app):
    result = list_audit_logs(action_filter="this.does.not.exist.anywhere")
    assert result["rows"] == []
    assert result["total"] == 0


# -- edge ------------------------------------------------------------------
def test_login_success_is_audit_logged(client, student_user):
    client.post(
        "/login",
        data={"email": student_user.email, "password": "password123"},
        follow_redirects=False,
    )
    entries = AuditLog.query.filter_by(action="auth.login_success").all()
    assert any(e.user_id == student_user.id for e in entries)


def test_login_failure_is_audit_logged(client, student_user):
    client.post(
        "/login",
        data={"email": student_user.email, "password": "wrong"},
        follow_redirects=False,
    )
    entries = AuditLog.query.filter_by(action="auth.login_failure").all()
    assert len(entries) >= 1


def test_recent_actions_returns_descending_order(app):
    log_action("first.event", commit=True)
    log_action("second.event", commit=True)
    log_action("third.event", commit=True)
    recent = recent_actions(limit=3)
    assert recent[0].action == "third.event"
    assert recent[-1].action == "first.event"
