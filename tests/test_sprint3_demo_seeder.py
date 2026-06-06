"""BP2T-181: Demo Data Seeder — unit tests."""

from app.models import User
from scripts.seed_demo import (
    ADMIN_PASSWORD,
    DEMO_PASSWORD,
    LECTURERS,
    STUDENTS,
    _ensure_lecturers,
    _ensure_students,
    _ensure_admin,
)


# -- positive --------------------------------------------------------------
def test_ensure_admin_returns_admin_user(app):
    admin = _ensure_admin()
    assert admin.role == "admin"


def test_ensure_students_creates_expected_count(app):
    students = _ensure_students()
    assert len(students) == len(STUDENTS)


def test_ensure_lecturers_creates_expected_count(app):
    lecturers = _ensure_lecturers()
    assert len(lecturers) == len(LECTURERS)


# -- negative (idempotency = no duplicates) -------------------------------
def test_seeder_is_idempotent_for_students(app):
    _ensure_students()
    count_after_first = User.query.filter_by(role="student").count()
    _ensure_students()
    count_after_second = User.query.filter_by(role="student").count()
    assert count_after_first == count_after_second


def test_seeder_is_idempotent_for_lecturers(app):
    _ensure_lecturers()
    count_after_first = User.query.filter_by(role="lecturer").count()
    _ensure_lecturers()
    count_after_second = User.query.filter_by(role="lecturer").count()
    assert count_after_first == count_after_second


def test_seeder_does_not_duplicate_admin(app):
    _ensure_admin()
    _ensure_admin()
    assert User.query.filter_by(role="admin").count() >= 1
    # No matter how many times we call, the original admin remains the only one
    admins = User.query.filter_by(email="admin@ante.local").all()
    assert len(admins) <= 1


# -- edge ------------------------------------------------------------------
def test_demo_student_names_are_hebrew(app):
    _ensure_students()
    students = User.query.filter_by(role="student").all()
    # at least one student should have Hebrew characters in their name
    hebrew_students = [s for s in students if any("֐" <= c <= "׿" for c in (s.full_name or ""))]
    assert hebrew_students


def test_demo_credentials_constants_are_strong_enough(app):
    assert len(DEMO_PASSWORD) >= 8
    assert len(ADMIN_PASSWORD) >= 8
