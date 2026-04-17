from flask import Blueprint, render_template, session, redirect, url_for
from app.models import db, ExerciseAttempt, User, ProgressRecord

progress_bp = Blueprint('progress', __name__)


@progress_bp.route('/progress')
def progress():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = db.session.get(User, user_id)
    attempts = (
        ExerciseAttempt.query
        .filter_by(user_id=user_id)
        .order_by(ExerciseAttempt.submitted_at.desc())
        .all()
    )
    record = ProgressRecord.query.filter_by(user_id=user_id).first()

    total_attempts = len(attempts)
    correct_attempts = sum(1 for a in attempts if a.is_correct)

    success_rate = 0
    if total_attempts > 0:
        success_rate = int((correct_attempts / total_attempts) * 100)

    return render_template(
        'progress.html',
        attempts=attempts,
        total_attempts=total_attempts,
        success_rate=success_rate,
        user=user,
        record=record,
    )
