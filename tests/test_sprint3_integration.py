"""Sprint 3 end-to-end integration tests.

Covers the three live-defense journeys plus the forgot-password flow.
"""

from app.models import (
    AuditLog,
    ExerciseAttempt,
    Module,
    ModuleProgress,
    PasswordResetToken,
    ProgressRecord,
    Question,
    SystemSetting,
    User,
    db,
)
from app.services.certificate_service import evaluate_certificate
from app.services.security_service import create_password_reset_token


# ============================================================
# Journey 1 — Admin end-to-end
# ============================================================
def test_admin_full_journey(client, admin_user, student_user, lecturer_user):
    # Login as admin
    login = client.post(
        "/login",
        data={"email": admin_user.email, "password": "password789"},
        follow_redirects=False,
    )
    assert login.status_code == 302
    assert "/admin/dashboard" in login.headers["Location"]

    # Visit dashboard
    dashboard = client.get("/admin/dashboard")
    assert dashboard.status_code == 200
    assert b"Administrator Dashboard" in dashboard.data

    # Visit user management
    users = client.get("/admin/users")
    assert users.status_code == 200
    assert student_user.email.encode() in users.data

    # Deactivate the student
    client.post(f"/admin/users/{student_user.id}/deactivate")
    refreshed = db.session.get(User, student_user.id)
    assert refreshed.is_active is False

    # View audit log — should contain the deactivation
    audit = client.get("/admin/audit")
    assert audit.status_code == 200
    assert b"user.deactivate" in audit.data

    # Download students CSV
    csv = client.get("/admin/reports/students.csv")
    assert csv.status_code == 200
    assert csv.mimetype.startswith("text/csv")
    assert csv.data.startswith("﻿".encode("utf-8"))  # UTF-8 BOM

    # Toggle maintenance mode on then off
    client.post(
        "/admin/settings",
        data={
            "system_name": "ANTE",
            "min_password_length": "8",
            "min_completion_score": "70",
            "maintenance_mode": "on",
        },
    )
    setting = db.session.get(SystemSetting, "maintenance_mode")
    assert setting.value == "1"

    client.post(
        "/admin/settings",
        data={
            "system_name": "ANTE",
            "min_password_length": "8",
            "min_completion_score": "70",
            # checkbox absent => off
        },
    )
    setting = db.session.get(SystemSetting, "maintenance_mode")
    assert setting.value == "0"

    # Logout
    logout = client.get("/logout", follow_redirects=False)
    assert logout.status_code == 302


# ============================================================
# Journey 2 — Lecturer end-to-end
# ============================================================
def test_lecturer_full_journey(client, lecturer_user, student_user):
    # Login
    login = client.post(
        "/login",
        data={"email": lecturer_user.email, "password": "password456"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    # Dashboard
    dashboard = client.get("/lecturer/dashboard")
    assert dashboard.status_code == 200

    # Create a question — first find Exercise module
    exercise = Module.query.filter(Module.name.ilike("exercise")).first()
    create_resp = client.post(
        "/lecturer/questions/new",
        data={
            "question_text": "Integration MCQ?",
            "question_type": "mcq",
            "correct_answer": "Yes",
            "explanation": "Because yes.",
            "difficulty": "easy",
            "module_id": str(exercise.id),
            "options": "Yes\nNo",
            "starter_code": "",
            "test_cases_json": "",
        },
        follow_redirects=False,
    )
    assert create_resp.status_code == 302
    new_q = Question.query.filter_by(question_text="Integration MCQ?").first()
    assert new_q is not None

    # Toggle it inactive
    client.post(f"/lecturer/questions/{new_q.id}/toggle")
    refreshed = db.session.get(Question, new_q.id)
    assert refreshed.is_active is False

    # Toggle back active
    client.post(f"/lecturer/questions/{new_q.id}/toggle")
    refreshed = db.session.get(Question, new_q.id)
    assert refreshed.is_active is True

    # Submissions screen renders
    submissions = client.get("/lecturer/submissions")
    assert submissions.status_code == 200

    # Logout
    logout = client.get("/logout", follow_redirects=False)
    assert logout.status_code == 302


# ============================================================
# Journey 3 — Student end-to-end including certificate
# ============================================================
def test_student_full_journey_with_certificate(client, student_user):
    # Login
    login = client.post(
        "/login",
        data={"email": student_user.email, "password": "password123"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    # Intro & Pipeline visits
    intro = client.get("/intro")
    assert intro.status_code == 200
    pipeline = client.get("/pipeline")
    assert pipeline.status_code == 200

    # Answer every active question correctly to qualify for the certificate
    questions = Question.query.filter_by(is_active=True).all()
    for q in questions:
        if q.question_type == "mcq":
            answer = q.correct_answer
            client.post(f"/exercise?q=0", data={"answer": answer})
        elif q.question_type == "open":
            client.post(f"/exercise?q=0", data={"open_answer": q.correct_answer})
        # we skip code questions in the integration (the sandbox is exercised separately)
        # mark progress directly for them
    # Force-complete the Exercise module to test certificate eligibility
    user_id = student_user.id
    exercise_mod = Module.query.filter(Module.name.ilike("exercise")).first()
    for module in Module.query.all():
        row = ModuleProgress.query.filter_by(user_id=user_id, module_id=module.id).first()
        if not row:
            row = ModuleProgress(user_id=user_id, module_id=module.id)
            db.session.add(row)
        row.completed = True
        row.progress_percentage = 100
    record = ProgressRecord.query.filter_by(user_id=user_id).first()
    if not record:
        record = ProgressRecord(user_id=user_id)
        db.session.add(record)
    # ensure success rate above min_completion_score
    if record.total_attempts == 0:
        record.total_attempts = 10
        record.correct_answers_count = 10
    record.exercise_completed = True
    db.session.commit()

    # Add at least one correct attempt per active question so unique-correct ratio is 100
    for q in questions:
        db.session.add(
            ExerciseAttempt(
                user_id=user_id, question_id=q.id, answer="x", is_correct=True, score=100
            )
        )
    db.session.commit()

    # Visit /certificate — should now be eligible
    cert = client.get("/certificate")
    assert cert.status_code == 200

    eligibility = evaluate_certificate(db.session.get(User, user_id))
    assert eligibility.eligible is True

    # Download the PDF
    pdf = client.get("/certificate/download")
    assert pdf.status_code == 200
    assert pdf.mimetype == "application/pdf"

    # Logout
    logout = client.get("/logout", follow_redirects=False)
    assert logout.status_code == 302


# ============================================================
# Journey 4 — Forgot password full cycle
# ============================================================
def test_forgot_then_reset_password_end_to_end(client, student_user):
    # Step 1: request reset
    request_resp = client.post(
        "/forgot-password",
        data={"email": student_user.email},
        follow_redirects=False,
    )
    assert request_resp.status_code == 302

    # A token should be in the DB
    token_row = PasswordResetToken.query.filter_by(user_id=student_user.id).first()
    assert token_row is not None
    assert token_row.used is False

    # Step 2: use the token to set a new password
    reset_resp = client.post(
        f"/reset-password/{token_row.token}",
        data={"password": "NewPass2026!", "confirm_password": "NewPass2026!"},
        follow_redirects=False,
    )
    assert reset_resp.status_code == 302
    assert "/login" in reset_resp.headers["Location"]

    # Step 3: old password no longer works
    old_login = client.post(
        "/login",
        data={"email": student_user.email, "password": "password123"},
        follow_redirects=False,
    )
    assert old_login.status_code == 302
    assert "/login" in old_login.headers["Location"]
    # (would log them in only with the new password)

    # Step 4: new password works
    new_login = client.post(
        "/login",
        data={"email": student_user.email, "password": "NewPass2026!"},
        follow_redirects=False,
    )
    assert new_login.status_code == 302
    # student goes to home, not /login
    assert "/login" not in new_login.headers["Location"]

    # Step 5: token cannot be reused
    refreshed = db.session.get(PasswordResetToken, token_row.token)
    assert refreshed.used is True
    second_use = client.post(
        f"/reset-password/{token_row.token}",
        data={"password": "Another1234!", "confirm_password": "Another1234!"},
        follow_redirects=False,
    )
    assert second_use.status_code == 302
    assert "/forgot-password" in second_use.headers["Location"]


# ============================================================
# Journey 5 — Lecturer reviews a student's code submission
# ============================================================
def test_lecturer_can_review_student_code_submission(client, student_user, lecturer_user):
    # Student creates a submission directly (simulating what /exercise does)
    code_q = Question.query.filter_by(question_type="code", is_active=True).first()
    if not code_q:
        return  # no code questions in this DB → skip silently
    attempt = ExerciseAttempt(
        user_id=student_user.id,
        question_id=code_q.id,
        answer="def solve(a, b):\n    return a + b\n",
        is_correct=True,
        score=100,
    )
    db.session.add(attempt)
    db.session.commit()

    # Lecturer logs in
    client.post(
        "/login",
        data={"email": lecturer_user.email, "password": "password456"},
        follow_redirects=False,
    )

    # Sees the submission listed
    listing = client.get("/lecturer/submissions")
    assert listing.status_code == 200
    assert student_user.full_name.encode() in listing.data

    # Opens detail page
    detail = client.get(f"/lecturer/submissions/{attempt.id}")
    assert detail.status_code == 200
    assert b"def solve" in detail.data

    # Posts a review comment
    review_post = client.post(
        f"/lecturer/submissions/{attempt.id}",
        data={"review_text": "Great work — concise and clean."},
        follow_redirects=False,
    )
    assert review_post.status_code == 302

    # Review is persisted
    refreshed = db.session.get(ExerciseAttempt, attempt.id)
    assert refreshed.lecturer_review == "Great work — concise and clean."
    assert refreshed.reviewed_by == lecturer_user.id
    assert refreshed.reviewed_at is not None

    # Audit log captured it
    log = AuditLog.query.filter_by(action="submission.review").first()
    assert log is not None
    assert log.target_id == attempt.id
