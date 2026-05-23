from flask import Blueprint, render_template, session, redirect, url_for
from app.models import ExerciseAttempt, ProgressRecord, User, db
from app.services.authz import login_required
from app.services.progress_service import build_module_states, build_progress_stats, get_demo_progress_context
from app.services.state_service import persist_learning_state

progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/progress')
@login_required
def progress():
    user_id = session.get('user_id')
    demo_mode = bool(session.get('demo_mode'))

    if demo_mode:
        demo = get_demo_progress_context()
        return render_template(
            'progress.html',
            attempts=[],
            total_attempts=demo["stats"].total_attempts,
            success_rate=demo["stats"].success_rate,
            user={"full_name": "Demo Lecturer", "role": "lecturer"},
            record=None,
            module_states=demo["module_states"],
            stats=demo["stats"],
            demo_mode=True,
        )

    if session.get("role") == "lecturer":
        return redirect(url_for("lecturer.lecturer_dashboard"))

    persist_learning_state(user_id, last_route="/progress")
    user = db.session.get(User, user_id)
    attempts = ExerciseAttempt.query.filter_by(user_id=user_id).order_by(ExerciseAttempt.submitted_at.desc()).all()
    record = ProgressRecord.query.filter_by(user_id=user_id).first()
    stats = build_progress_stats(record, user_id)
    module_states = build_module_states(record, user_id=user_id)
    db.session.commit()

    return render_template(
        'progress.html',
        attempts=attempts,
        total_attempts=stats.total_attempts,
        success_rate=stats.success_rate,
        user=user,
        record=record,
        module_states=module_states,
        stats=stats,
        demo_mode=False,
    )
