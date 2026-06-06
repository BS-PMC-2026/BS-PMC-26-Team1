from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.models import db
from app.services.authz import student_required
from app.services.progress_service import mark_module_completed, update_module_progress_percent
from app.services.state_service import persist_learning_state
from app.services.theory_service import get_theory_content_by_module_name

pipeline_bp = Blueprint('pipeline', __name__)

@pipeline_bp.route('/pipeline')
@student_required
def pipeline():
    user_id = session.get('user_id')
    demo_mode = bool(session.get('demo_mode'))
    if not user_id and not demo_mode:
        flash('Session missing. Please login to continue.', 'error')
        return redirect(url_for('auth.login'))

    if not demo_mode:
        mark_module_completed(user_id, 'pipeline')
        update_module_progress_percent(user_id, "Pipeline", 100, completed=True)
        persist_learning_state(user_id, current_module_name="Pipeline", last_route="/pipeline")
        db.session.commit()

    theory_content = get_theory_content_by_module_name("Pipeline")
    return render_template('pipeline.html', theory_content=theory_content)
