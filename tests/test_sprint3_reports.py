"""BP2T-167: Admin Export Reports (CSV) — unit tests."""

from app.models import AuditLog
from app.services.report_service import (
    REPORT_BUILDERS,
    build_questions_report,
    build_students_report,
    build_usage_report,
)


# -- positive --------------------------------------------------------------
def test_reports_index_renders(auth_admin_client):
    response = auth_admin_client.get("/admin/reports")
    assert response.status_code == 200
    assert b"Reports" in response.data


def test_students_report_includes_header(app):
    rows, blob = build_students_report(None, None)
    assert rows[0][:3] == ["User ID", "Full Name", "Email"]
    # UTF-8 BOM at the start so Excel reads Hebrew correctly
    assert blob.startswith("﻿".encode("utf-8"))


def test_questions_report_csv_downloads(auth_admin_client):
    response = auth_admin_client.get("/admin/reports/questions.csv")
    assert response.status_code == 200
    assert response.mimetype.startswith("text/csv")
    assert b"Question ID" in response.data


# -- negative --------------------------------------------------------------
def test_unknown_report_returns_404(auth_admin_client):
    response = auth_admin_client.get("/admin/reports/does-not-exist.csv")
    assert response.status_code == 404


def test_reports_blocked_for_non_admin(auth_student_client):
    response = auth_student_client.get("/admin/reports/students.csv", follow_redirects=False)
    assert response.status_code == 302


# -- edge ------------------------------------------------------------------
def test_usage_report_handles_empty_database(app):
    rows, blob = build_usage_report(None, None)
    assert rows[0][:2] == ["Date", "Attempts"]
    assert len(rows) >= 2  # header + at least one date row


def test_each_report_key_is_builder(app):
    assert set(REPORT_BUILDERS.keys()) == {"students", "questions", "usage"}
    for builder in REPORT_BUILDERS.values():
        rows, blob = builder(None, None)
        assert isinstance(rows, list)
        assert isinstance(blob, (bytes, bytearray))


def test_report_download_is_audit_logged(auth_admin_client):
    auth_admin_client.get("/admin/reports/students.csv")
    entries = AuditLog.query.filter_by(action="report.download").all()
    assert len(entries) >= 1
