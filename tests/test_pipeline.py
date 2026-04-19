"""Tests for the Pipeline visualization route."""

from app.models import db, ProgressRecord


class TestPipelineAccess:

    def test_redirects_to_login_when_unauthenticated(self, client):
        rv = client.get("/pipeline", follow_redirects=False)
        assert rv.status_code == 302
        assert "/login" in rv.headers.get("Location", "")

    def test_loads_for_authenticated_user(self, auth_client):
        rv = auth_client.get("/pipeline")
        assert rv.status_code == 200


class TestPipelineContent:

    def test_contains_pipeline_stages(self, auth_client):
        rv = auth_client.get("/pipeline")
        data = rv.data
        assert b"Code" in data
        assert b"Build" in data
        assert b"Test" in data
        assert b"Deploy" in data

    def test_has_exercise_link(self, auth_client):
        rv = auth_client.get("/pipeline")
        assert b"/exercise" in rv.data


class TestPipelineProgress:

    def test_marks_pipeline_viewed(self, auth_client, sample_student):
        auth_client.get("/pipeline")

        record = ProgressRecord.query.filter_by(user_id=sample_student["id"]).first()
        assert record is not None
        assert record.pipeline_viewed is True

    def test_creates_progress_record_if_missing(self, auth_client, sample_student):
        auth_client.get("/pipeline")

        record = ProgressRecord.query.filter_by(user_id=sample_student["id"]).first()
        assert record is not None

    def test_repeat_visit_does_not_duplicate(self, auth_client, sample_student):
        auth_client.get("/pipeline")
        auth_client.get("/pipeline")

        records = ProgressRecord.query.filter_by(user_id=sample_student["id"]).all()
        assert len(records) == 1
