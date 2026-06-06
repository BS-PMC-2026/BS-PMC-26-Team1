"""
Demo data seeder for the ANTE platform.

Generates:
  * 1 admin (re-used if already present)
  * 2 lecturers
  * 12 students with Hebrew names
  * 8-12 additional exercise questions (mixed MCQ / OPEN / CODE)
  * 5-15 attempts per student with realistic pass/fail spread
  * Expanded theory content for Intro / Pipeline modules

Idempotent: re-running does not create duplicates (same usernames / emails / texts).
Writes credentials to DEMO_USERS.md at the project root.

Usage:
  python scripts/seed_demo.py
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Allow `python scripts/seed_demo.py` to find the `app` package.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from werkzeug.security import generate_password_hash  # noqa: E402

from app import create_app  # noqa: E402
from app.models import (  # noqa: E402
    AdminProfile,
    ExerciseAttempt,
    LecturerProfile,
    Module,
    Question,
    StudentProfile,
    TheoryContent,
    User,
    db,
)
from app.services.code_runner_service import (  # noqa: E402
    default_compiler_label,
    default_environment_label,
    normalize_language,
)


DEMO_PASSWORD = "Demo#12345"
ADMIN_PASSWORD = "Admin#12345"

LECTURERS = [
    {
        "username": "lecturer.ravid",
        "full_name": "ד\"ר רביד כהן",
        "email": "ravid.cohen@ante.local",
        "department": "Software Engineering",
        "academic_title": "Senior Lecturer",
    },
    {
        "username": "lecturer.shira",
        "full_name": "ד\"ר שירה לוי",
        "email": "shira.levy@ante.local",
        "department": "Computer Science",
        "academic_title": "Associate Professor",
    },
]

STUDENTS = [
    ("נועה אברהמי", "noa.avrahami@ante.local"),
    ("יוסי בן-דוד", "yossi.bendavid@ante.local"),
    ("מאיה דהן", "maya.dahan@ante.local"),
    ("איתי חיים", "itai.haim@ante.local"),
    ("שירה כהן", "shira.cohen@ante.local"),
    ("דניאל לוי", "daniel.levy@ante.local"),
    ("רוני מזרחי", "roni.mizrahi@ante.local"),
    ("עומר נגר", "omer.nagar@ante.local"),
    ("הילה סבן", "hila.saban@ante.local"),
    ("אורי פרץ", "ori.peretz@ante.local"),
    ("עדי צור", "adi.tzur@ante.local"),
    ("יהונתן רז", "yehonatan.raz@ante.local"),
]

EXTRA_QUESTIONS = [
    {
        "type": "mcq",
        "question_text": "What is the primary role of a CI server?",
        "correct_answer": "Automate builds and tests on every commit",
        "options": [
            "Manually deploy to production",
            "Automate builds and tests on every commit",
            "Write documentation for new features",
        ],
        "explanation": "CI servers detect commits and automatically build and test the code.",
        "difficulty": "easy",
    },
    {
        "type": "mcq",
        "question_text": "Which artifact is typically produced by the build stage?",
        "correct_answer": "A deployable container image or package",
        "options": [
            "A spreadsheet of test results",
            "A deployable container image or package",
            "A list of pending tickets",
        ],
        "explanation": "Build stages compile code into a deployable artifact such as a Docker image or JAR.",
        "difficulty": "easy",
    },
    {
        "type": "mcq",
        "question_text": "What does 'shift left' mean in CI/CD?",
        "correct_answer": "Move testing and quality checks earlier in the pipeline",
        "options": [
            "Move releases to the left of the calendar",
            "Move testing and quality checks earlier in the pipeline",
            "Run unit tests in production only",
        ],
        "explanation": "Shift-left moves verification activities earlier so defects are caught sooner.",
        "difficulty": "medium",
    },
    {
        "type": "mcq",
        "question_text": "Why are pipeline stages typically isolated environments?",
        "correct_answer": "To produce reproducible, side-effect-free builds and tests",
        "options": [
            "Because developers prefer many terminals",
            "To produce reproducible, side-effect-free builds and tests",
            "Because Docker requires it for licensing",
        ],
        "explanation": "Isolated stages keep builds reproducible and prevent contamination between runs.",
        "difficulty": "medium",
    },
    {
        "type": "open",
        "question_text": "Explain in your own words the difference between Continuous Delivery and Continuous Deployment.",
        "correct_answer": "delivery|deployment|manual approval|automatic release",
        "options": [],
        "explanation": "Continuous Delivery stops at a deployable artifact awaiting approval; Continuous Deployment goes all the way to production automatically.",
        "difficulty": "medium",
    },
    {
        "type": "open",
        "question_text": "Name one practical benefit of running automated tests on every commit.",
        "correct_answer": "feedback|catch bugs|regression|fast|early|confidence",
        "options": [],
        "explanation": "Fast feedback, early bug detection, and confidence to refactor are common benefits.",
        "difficulty": "easy",
    },
    {
        "type": "code",
        "question_text": "Write a function solve(a, b) that returns the absolute difference between a and b.",
        "correct_answer": "def solve(a, b):",
        "options": [],
        "explanation": "Subtract one from the other and return the absolute value.",
        "difficulty": "easy",
        "starter_code": "def solve(a, b):\n    # return abs(a - b)\n    pass",
        "test_cases": [
            {"inputs": [5, 2], "expected": 3},
            {"inputs": [-3, -10], "expected": 7},
            {"inputs": [4, 4], "expected": 0},
        ],
    },
    {
        "type": "code",
        "question_text": "Write a function solve(a, b) that returns the larger of a and b.",
        "correct_answer": "def solve(a, b):",
        "options": [],
        "explanation": "Return the maximum of the two arguments.",
        "difficulty": "easy",
        "starter_code": "def solve(a, b):\n    # return max(a, b)\n    pass",
        "test_cases": [
            {"inputs": [3, 9], "expected": 9},
            {"inputs": [-2, -5], "expected": -2},
            {"inputs": [7, 7], "expected": 7},
        ],
    },
    {
        "type": "mcq",
        "question_text": "Which practice helps to recover quickly from a bad deployment?",
        "correct_answer": "Automated rollback",
        "options": ["Manual hotfix", "Automated rollback", "Skipping tests"],
        "explanation": "Automated rollback restores the previous known-good version with minimal manual effort.",
        "difficulty": "easy",
    },
    {
        "type": "mcq",
        "question_text": "What does an artifact repository do in a CI/CD pipeline?",
        "correct_answer": "Stores versioned build outputs for downstream deployment",
        "options": [
            "Runs developer interviews",
            "Stores versioned build outputs for downstream deployment",
            "Replaces the source code repository",
        ],
        "explanation": "Artifact repositories keep deployable outputs versioned and available for promotion across environments.",
        "difficulty": "medium",
    },
]


def _ensure_admin():
    admin = User.query.filter_by(role="admin").first()
    if admin:
        return admin
    admin = User(
        username="admin",
        full_name="System Administrator",
        email="admin@ante.local",
        password_hash=generate_password_hash(ADMIN_PASSWORD),
        role="admin",
        is_active=True,
    )
    db.session.add(admin)
    db.session.flush()
    db.session.add(AdminProfile(user_id=admin.id, admin_id="ADMIN-001", scope="full"))
    return admin


def _ensure_lecturers() -> List[User]:
    created: List[User] = []
    for data in LECTURERS:
        existing = User.query.filter_by(email=data["email"]).first()
        if existing:
            created.append(existing)
            continue
        user = User(
            username=data["username"],
            full_name=data["full_name"],
            email=data["email"],
            password_hash=generate_password_hash(DEMO_PASSWORD),
            role="lecturer",
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(
            LecturerProfile(
                user_id=user.id,
                lecturer_id=data["username"].split(".")[-1].upper(),
                department=data["department"],
                academic_title=data["academic_title"],
            )
        )
        created.append(user)
    return created


def _ensure_students() -> List[User]:
    created: List[User] = []
    for full_name, email in STUDENTS:
        existing = User.query.filter_by(email=email).first()
        if existing:
            created.append(existing)
            continue
        username = email.split("@")[0]
        user = User(
            username=username,
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(DEMO_PASSWORD),
            role="student",
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(
            StudentProfile(
                user_id=user.id,
                student_id=username.upper(),
                department="Software Engineering",
                year_of_study=random.choice([1, 2, 3]),
            )
        )
        created.append(user)
    return created


def _ensure_extra_questions(exercise_module: Module, author_id: int) -> int:
    inserted = 0
    existing_texts = {q.question_text for q in Question.query.all()}
    for data in EXTRA_QUESTIONS:
        if data["question_text"] in existing_texts:
            continue
        starter_code = data.get("starter_code") if data["type"] == "code" else None
        test_cases = data.get("test_cases") if data["type"] == "code" else None
        lang = normalize_language("python") if data["type"] == "code" else None
        question = Question(
            question_text=data["question_text"],
            question_type=data["type"],
            options_json=json.dumps(data.get("options", [])),
            correct_answer=data["correct_answer"],
            explanation=data["explanation"],
            difficulty=data.get("difficulty", "medium"),
            module_id=exercise_module.id,
            starter_code=starter_code,
            test_cases_json=json.dumps(test_cases) if test_cases else None,
            language=lang,
            execution_environment=default_environment_label(lang) if lang else None,
            compiler_info=default_compiler_label(lang) if lang else None,
            created_by=author_id,
            is_active=True,
        )
        db.session.add(question)
        inserted += 1
    return inserted


def _ensure_theory_expansion(modules_by_name: dict, author_id: int) -> None:
    intro = modules_by_name.get("intro")
    pipeline = modules_by_name.get("pipeline")
    if intro:
        row = TheoryContent.query.filter_by(module_id=intro.id).first()
        if row:
            row.headline = "CI/CD Foundations"
            row.explanation = (
                "CI/CD is the backbone of modern software delivery. "
                "It combines disciplined version control, automated testing, and reliable deployment "
                "to keep features flowing safely from developer laptops to production systems. "
                "Teams adopt it to reduce risk, accelerate feedback, and increase confidence in every change."
            )
            row.examples = (
                "Example 1: A small feature branch is merged automatically after green tests. \n"
                "Example 2: A failed lint check blocks the merge until fixed.\n"
                "Example 3: A nightly build publishes a release candidate to staging for review."
            )
            row.updated_by = author_id
    if pipeline:
        row = TheoryContent.query.filter_by(module_id=pipeline.id).first()
        if row:
            row.headline = "Pipeline Stages in Practice"
            row.explanation = (
                "A pipeline is the contract between development and operations. "
                "Each stage – Code, Build, Test, Deploy – validates the artifact a little further. "
                "Strong pipelines are reproducible, observable, and reversible: "
                "if anything fails, the team should learn fast and roll back quickly."
            )
            row.examples = (
                "Example 1: Code commit triggers a unit-test pipeline run.\n"
                "Example 2: Build packages the app into a Docker image.\n"
                "Example 3: Test stage runs integration suites with seed data.\n"
                "Example 4: Deploy promotes the image to staging and then production after approval."
            )
            row.updated_by = author_id


def _ensure_attempts(students: List[User]) -> int:
    questions = Question.query.filter_by(is_active=True).all()
    if not questions:
        return 0
    created = 0
    for student in students:
        existing = ExerciseAttempt.query.filter_by(user_id=student.id).count()
        if existing >= 5:
            continue
        attempts_target = random.randint(5, 15)
        sample = random.sample(questions, k=min(attempts_target, len(questions)))
        base_time = datetime.utcnow() - timedelta(days=random.randint(1, 10))
        for offset, question in enumerate(sample):
            is_correct = random.random() < 0.7
            attempt = ExerciseAttempt(
                user_id=student.id,
                question_id=question.id,
                answer=question.correct_answer if is_correct else "demo-incorrect-answer",
                submitted_output="demo run output",
                is_correct=is_correct,
                feedback_text=("Correct" if is_correct else "Incorrect") + " | demo seeded attempt",
                score=100 if is_correct else 25,
                submitted_at=base_time + timedelta(hours=offset),
            )
            db.session.add(attempt)
            created += 1
    return created


def _refresh_analytics(students: List[User]) -> None:
    from app.services.analytics_service import refresh_user_analytics
    from app.services.progress_service import (
        mark_module_completed,
        record_exercise_attempt,
    )

    for student in students:
        attempts = ExerciseAttempt.query.filter_by(user_id=student.id).all()
        for attempt in attempts:
            record_exercise_attempt(
                user_id=student.id,
                question_id=attempt.question_id,
                is_correct=attempt.is_correct,
            )
        mark_module_completed(student.id, "intro")
        mark_module_completed(student.id, "pipeline")
        refresh_user_analytics(student.id)


def _write_demo_users_md(students: List[User], lecturers: List[User]) -> Path:
    out_path = ROOT / "DEMO_USERS.md"
    lines = ["# ANTE Demo Credentials", ""]
    lines.append("These accounts are seeded by `python scripts/seed_demo.py` for the live demo.\n")
    lines.append("All accounts share the same demo password unless stated otherwise.\n")
    lines.append("")
    lines.append("## Administrator")
    lines.append("")
    lines.append("| Email | Password |")
    lines.append("|-------|----------|")
    lines.append(f"| admin@ante.local | {ADMIN_PASSWORD} |")
    lines.append("")
    lines.append("## Lecturers")
    lines.append("")
    lines.append("| Name | Email | Password |")
    lines.append("|------|-------|----------|")
    for lecturer in lecturers:
        lines.append(f"| {lecturer.full_name} | {lecturer.email} | {DEMO_PASSWORD} |")
    lines.append("")
    lines.append("## Students")
    lines.append("")
    lines.append("| Name | Email | Password |")
    lines.append("|------|-------|----------|")
    for student in students:
        lines.append(f"| {student.full_name} | {student.email} | {DEMO_PASSWORD} |")
    lines.append("")
    lines.append("> ⚠️ Do NOT commit this file to source control. It is git-ignored by default.")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def run() -> dict:
    random.seed(42)
    app = create_app()
    with app.app_context():
        admin = _ensure_admin()
        lecturers = _ensure_lecturers()
        students = _ensure_students()
        modules_by_name = {m.name.lower(): m for m in Module.query.all()}
        exercise_module = modules_by_name.get("exercise")
        if not exercise_module:
            raise RuntimeError("Exercise module missing — run the app once before seeding demo data.")
        questions_added = _ensure_extra_questions(exercise_module, lecturers[0].id if lecturers else admin.id)
        _ensure_theory_expansion(modules_by_name, lecturers[0].id if lecturers else admin.id)
        db.session.commit()

        attempts_added = _ensure_attempts(students)
        db.session.commit()
        _refresh_analytics(students)
        db.session.commit()

        out_path = _write_demo_users_md(students, lecturers)

        return {
            "admin": admin.email,
            "lecturers": [u.email for u in lecturers],
            "students": [u.email for u in students],
            "questions_added": questions_added,
            "attempts_added": attempts_added,
            "demo_users_file": str(out_path),
        }


if __name__ == "__main__":
    summary = run()
    print("Demo seed complete:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
