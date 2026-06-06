from flask import Blueprint, jsonify, render_template, session, redirect, url_for
from app.models import ProgressRecord, db
from app.services.progress_service import build_module_states, build_progress_stats, get_demo_progress_context
from app.services.state_service import get_or_create_learning_state, persist_learning_state

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    is_authenticated = bool(session.get('user_id')) or bool(session.get('demo_mode'))
    return render_template('home.html', is_authenticated=is_authenticated)

@main_bp.route('/start')
def start():
    if session.get('demo_mode'):
        return redirect(url_for('main.demo_view'))
    if session.get('user_id'):
        if session.get("role") == "admin":
            return redirect(url_for("admin.dashboard"))
        if session.get("role") == "lecturer":
            return redirect(url_for("lecturer.lecturer_dashboard"))
        return redirect(url_for('intro.intro'))
    else:
        return redirect(url_for('auth.login'))

@main_bp.route('/learning-path')
def learning_path():
    user_id = session.get('user_id')
    demo_mode = bool(session.get('demo_mode'))
    if not user_id and not demo_mode:
        return redirect(url_for('auth.login'))
    if session.get("role") == "lecturer" and not demo_mode:
        return redirect(url_for("lecturer.lecturer_dashboard"))
    if session.get("role") == "admin" and not demo_mode:
        return redirect(url_for("admin.dashboard"))

    if demo_mode:
        demo = get_demo_progress_context()
        return render_template(
            'learning_path.html',
            record=None,
            module_states=demo["module_states"],
            stats=demo["stats"],
            demo_mode=True,
        )

    record = ProgressRecord.query.filter_by(user_id=user_id).first()
    persist_learning_state(user_id, last_route="/learning-path")
    module_states = build_module_states(record, user_id=user_id)
    stats = build_progress_stats(record, user_id)
    db.session.commit()
    return render_template(
        'learning_path.html',
        record=record,
        module_states=module_states,
        stats=stats,
        demo_mode=False,
    )


@main_bp.route('/demo-view')
def demo_view():
    if not session.get('demo_mode'):
        return redirect(url_for('auth.login'))

    demo = get_demo_progress_context()
    return render_template(
        'demo_view.html',
        module_states=demo["module_states"],
        stats=demo["stats"],
    )


@main_bp.route('/flow/validate')
def flow_validate():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    record = ProgressRecord.query.filter_by(user_id=user_id).first()
    learning_state = get_or_create_learning_state(user_id)
    persist_learning_state(user_id, last_route="/flow/validate")
    module_states = build_module_states(record, user_id=user_id)
    stats = build_progress_stats(record, user_id)
    next_route = '/progress'
    for module_state in module_states:
        if not module_state["completed"]:
            next_route = module_state["route"]
            break
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "user_id": user_id,
            "next_route": next_route,
            "modules_completed": stats.modules_completed,
            "modules_total": stats.modules_total,
            "module_percent": stats.module_percent,
            "last_route": learning_state.last_route,
        }
    )
