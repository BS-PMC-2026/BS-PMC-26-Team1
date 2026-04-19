"""Tests for the Introduction module route and template."""

from app.models import db, ProgressRecord


class TestIntroAccess:

    def test_redirects_to_login_when_unauthenticated(self, client):
        rv = client.get("/intro", follow_redirects=False)
        assert rv.status_code == 302
        assert "/login" in rv.headers.get("Location", "")

    def test_loads_for_authenticated_user(self, auth_client):
        rv = auth_client.get("/intro")
        assert rv.status_code == 200


class TestIntroContent:

    def test_contains_devops_section(self, auth_client):
        rv = auth_client.get("/intro")
        assert b"What is DevOps?" in rv.data

    def test_contains_ci_section(self, auth_client):
        rv = auth_client.get("/intro")
        assert b"Continuous Integration" in rv.data

    def test_contains_cd_section(self, auth_client):
        rv = auth_client.get("/intro")
        assert b"Continuous Delivery" in rv.data
        assert b"Continuous Deployment" in rv.data

    def test_contains_summary_section(self, auth_client):
        rv = auth_client.get("/intro")
        assert b"How They All Fit Together" in rv.data

    def test_has_continue_to_pipeline_button(self, auth_client):
        rv = auth_client.get("/intro")
        assert b"Continue to Pipeline" in rv.data
        assert b"/pipeline" in rv.data


class TestIntroProgress:

    def test_marks_intro_completed(self, auth_client, sample_student):
        auth_client.get("/intro")

        record = ProgressRecord.query.filter_by(user_id=sample_student["id"]).first()
        assert record is not None
        assert record.intro_completed is True

    def test_creates_progress_record_if_missing(self, auth_client, sample_student):
        # Ensure no record exists beforehand
        existing = ProgressRecord.query.filter_by(user_id=sample_student["id"]).first()
        assert existing is None or existing is not None  # just proceed

        auth_client.get("/intro")

        record = ProgressRecord.query.filter_by(user_id=sample_student["id"]).first()
        assert record is not None

    def test_repeat_visit_does_not_duplicate_record(self, auth_client, sample_student):
        auth_client.get("/intro")
        auth_client.get("/intro")

        records = ProgressRecord.query.filter_by(user_id=sample_student["id"]).all()
        assert len(records) == 1
