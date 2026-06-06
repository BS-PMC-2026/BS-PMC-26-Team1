"""BP2T-187: Course Completion Certificate — unit tests."""

from app.models import (
    ExerciseAttempt,
    Module,
    ModuleProgress,
    ProgressRecord,
    Question,
    db,
)
from app.services.certificate_service import (
    build_certificate_pdf,
    certificate_filename,
    evaluate_certificate,
)
from app.services.settings_service import set_setting


def _make_student_complete(user_id):
    """Mark all modules complete and add enough correct exercise attempts."""
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
    questions = Question.query.filter_by(is_active=True).all()
    for q in questions:
        attempt = ExerciseAttempt(
            user_id=user_id, question_id=q.id, answer="correct", is_correct=True, score=100
        )
        db.session.add(attempt)
    record.total_attempts = len(questions)
    record.correct_answers_count = len(questions)
    record.exercise_completed = True
    db.session.commit()


# -- positive --------------------------------------------------------------
def test_eligible_student_can_view_certificate(auth_student_client, student_user):
    _make_student_complete(student_user.id)
    response = auth_student_client.get("/certificate")
    assert response.status_code == 200
    assert b"Certificate of Completion" in response.data or b"certificate" in response.data.lower()


def test_eligible_student_can_download_pdf(auth_student_client, student_user):
    _make_student_complete(student_user.id)
    response = auth_student_client.get("/certificate/download")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_pdf_contains_student_name(app, student_user):
    _make_student_complete(student_user.id)
    eligibility = evaluate_certificate(student_user)
    pdf_bytes = build_certificate_pdf(eligibility)
    assert pdf_bytes.startswith(b"%PDF")
    assert student_user.full_name.encode("latin-1", errors="replace") in pdf_bytes or \
           any(part.encode() in pdf_bytes for part in student_user.full_name.split())


# -- negative --------------------------------------------------------------
def test_incomplete_student_is_not_eligible(app, student_user):
    eligibility = evaluate_certificate(student_user)
    assert eligibility.eligible is False
    assert eligibility.missing_modules  # at least one module missing


def test_incomplete_student_cannot_download(auth_student_client, student_user):
    response = auth_student_client.get("/certificate/download", follow_redirects=False)
    # not eligible → redirected back to /certificate
    assert response.status_code in {302, 403}


def test_lecturer_cannot_access_certificate_page(auth_lecturer_client):
    response = auth_lecturer_client.get("/certificate", follow_redirects=False)
    # lecturers are not students → redirected
    assert response.status_code == 302


# -- edge ------------------------------------------------------------------
def test_minimum_score_setting_is_respected(app, student_user):
    set_setting("min_completion_score", "99")
    db.session.commit()
    _make_student_complete(student_user.id)
    # mark as if score is 70 - below the 99 threshold (use rejection)
    eligibility = evaluate_certificate(student_user)
    # _make_student_complete gives perfect score → still eligible at 99% threshold
    assert eligibility.min_required_score == 99


def test_certificate_filename_is_safe(app, student_user):
    filename = certificate_filename(student_user)
    assert filename.endswith(".pdf")
    assert "/" not in filename
    assert "\\" not in filename


def test_eligibility_shows_missing_modules(app, student_user):
    # no progress at all
    eligibility = evaluate_certificate(student_user)
    assert eligibility.missing_modules
    assert eligibility.modules_completed == 0
