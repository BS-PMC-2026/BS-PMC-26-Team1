"""Tests for SQLAlchemy models – creation, defaults, and relationships."""

from datetime import datetime
from werkzeug.security import generate_password_hash

from app.models import db, User, StudentProfile, LecturerProfile, ProgressRecord, ExerciseAttempt


class TestUserModel:
    """User model creation and defaults."""

    def test_create_user(self, app):
        user = User(
            full_name="Alice", email="alice@test.com",
            password_hash=generate_password_hash("secret12"),
            role="student",
        )
        db.session.add(user)
        db.session.commit()

        fetched = User.query.filter_by(email="alice@test.com").first()
        assert fetched is not None
        assert fetched.full_name == "Alice"
        assert fetched.role == "student"

    def test_user_is_active_by_default(self, app):
        user = User(
            full_name="Bob", email="bob@test.com",
            password_hash="hash", role="lecturer",
        )
        db.session.add(user)
        db.session.commit()

        assert user.is_active is True

    def test_user_created_at_auto_set(self, app):
        user = User(
            full_name="Carol", email="carol@test.com",
            password_hash="hash", role="student",
        )
        db.session.add(user)
        db.session.commit()

        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)


class TestStudentProfile:
    """StudentProfile relationship and defaults."""

    def test_student_profile_relationship(self, app):
        user = User(full_name="Dan", email="dan@test.com",
                     password_hash="hash", role="student")
        db.session.add(user)
        db.session.flush()

        profile = StudentProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()

        assert user.student_profile is not None
        assert user.student_profile.progress_percent == 0

    def test_student_profile_default_values(self, app):
        user = User(full_name="Eve", email="eve@test.com",
                     password_hash="hash", role="student")
        db.session.add(user)
        db.session.flush()

        profile = StudentProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()

        assert profile.student_id is None
        assert profile.department is None
        assert profile.year_of_study is None
        assert profile.progress_percent == 0


class TestLecturerProfile:
    """LecturerProfile relationship and defaults."""

    def test_lecturer_profile_relationship(self, app):
        user = User(full_name="Frank", email="frank@test.com",
                     password_hash="hash", role="lecturer")
        db.session.add(user)
        db.session.flush()

        profile = LecturerProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()

        assert user.lecturer_profile is not None


class TestProgressRecord:
    """ProgressRecord defaults and updates."""

    def test_defaults(self, app):
        user = User(full_name="Grace", email="grace@test.com",
                     password_hash="hash", role="student")
        db.session.add(user)
        db.session.flush()

        record = ProgressRecord(user_id=user.id)
        db.session.add(record)
        db.session.commit()

        assert record.intro_completed is False
        assert record.pipeline_viewed is False
        assert record.exercise_completed is False
        assert record.correct_answers_count == 0
        assert record.total_attempts == 0
        assert record.score == 0

    def test_update_progress(self, app):
        user = User(full_name="Hank", email="hank@test.com",
                     password_hash="hash", role="student")
        db.session.add(user)
        db.session.flush()

        record = ProgressRecord(user_id=user.id)
        db.session.add(record)
        db.session.commit()

        record.intro_completed = True
        record.total_attempts = 5
        record.correct_answers_count = 3
        db.session.commit()

        fetched = ProgressRecord.query.filter_by(user_id=user.id).first()
        assert fetched.intro_completed is True
        assert fetched.total_attempts == 5
        assert fetched.correct_answers_count == 3


class TestExerciseAttempt:
    """ExerciseAttempt creation and timestamp alias."""

    def test_defaults(self, app):
        user = User(full_name="Ivy", email="ivy@test.com",
                     password_hash="hash", role="student")
        db.session.add(user)
        db.session.flush()

        attempt = ExerciseAttempt(user_id=user.id, is_correct=True,
                                  feedback_text="Good job")
        db.session.add(attempt)
        db.session.commit()

        assert attempt.is_correct is True
        assert attempt.score == 0
        assert attempt.submitted_at is not None

    def test_timestamp_alias(self, app):
        """The .timestamp property should return .submitted_at for template compat."""
        user = User(full_name="Jack", email="jack@test.com",
                     password_hash="hash", role="student")
        db.session.add(user)
        db.session.flush()

        attempt = ExerciseAttempt(user_id=user.id)
        db.session.add(attempt)
        db.session.commit()

        assert attempt.timestamp == attempt.submitted_at
