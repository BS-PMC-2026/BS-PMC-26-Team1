from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from io import BytesIO

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from sqlalchemy import func
from werkzeug.security import generate_password_hash

from app.models import (
    AdminProfile,
    AuditLog,
    ExerciseAttempt,
    LecturerProfile,
    Module,
    ProgressRecord,
    StudentProfile,
    SystemSetting,
    TheoryContent,
    User,
    db,
)
from app.services.audit_service import list_audit_logs, log_action, recent_actions
from app.services.authz import admin_required
from app.services.report_service import REPORT_BUILDERS, REPORT_LABELS
from app.services.security_service import (
    validate_csrf_token,
    validate_email,
    validate_password,
    validate_text_field,
)
from app.services.settings_service import (
    DEFAULT_SETTINGS,
    all_settings,
    get_setting,
    get_setting_int,
    set_setting,
)
from app.services.user_admin_service import (
    count_admins,
    delete_user_cascade,
    find_user,
    list_users,
    set_active,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _csrf_ok() -> bool:
    return validate_csrf_token(request.form.get("csrf_token"))


def _require_csrf_or_redirect(redirect_target: str):
    if not _csrf_ok():
        flash("Security check failed. Please retry the action.", "error")
        return redirect(redirect_target)
    return None


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    total_students = User.query.filter_by(role="student").count()
    total_lecturers = User.query.filter_by(role="lecturer").count()
    total_admins = User.query.filter_by(role="admin").count()
    total_attempts = ExerciseAttempt.query.count()
    correct_attempts = ExerciseAttempt.query.filter(ExerciseAttempt.is_correct.is_(True)).count()
    overall_success = int((correct_attempts / total_attempts) * 100) if total_attempts else 0

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    activity_rows = (
        db.session.query(
            func.date(ExerciseAttempt.submitted_at).label("day"),
            func.count(ExerciseAttempt.id).label("count"),
        )
        .filter(ExerciseAttempt.submitted_at >= seven_days_ago)
        .group_by(func.date(ExerciseAttempt.submitted_at))
        .order_by(func.date(ExerciseAttempt.submitted_at).asc())
        .all()
    )
    activity = [{"date": str(row.day), "count": int(row.count)} for row in activity_rows]

    audit_entries = recent_actions(limit=5)

    return render_template(
        "admin/dashboard.html",
        stats={
            "students": total_students,
            "lecturers": total_lecturers,
            "admins": total_admins,
            "attempts": total_attempts,
            "success_average": overall_success,
        },
        activity=activity,
        audit_entries=audit_entries,
    )


@admin_bp.route("/users")
@admin_required
def users():
    page = max(1, int(request.args.get("page", 1) or 1))
    search = (request.args.get("q") or "").strip()
    role_filter = (request.args.get("role") or "").strip()
    status_filter = (request.args.get("status") or "").strip()
    paged = list_users(
        page=page,
        per_page=20,
        search=search,
        role_filter=role_filter,
        status_filter=status_filter,
    )
    return render_template(
        "admin/users.html",
        paged=paged,
        search=search,
        role_filter=role_filter,
        status_filter=status_filter,
    )


@admin_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@admin_required
def activate_user(user_id: int):
    bad = _require_csrf_or_redirect(url_for("admin.users"))
    if bad:
        return bad
    user = find_user(user_id)
    if not user:
        abort(404)
    if user.role == "admin" and user.id == session.get("user_id"):
        flash("Administrators cannot toggle their own status.", "error")
        return redirect(url_for("admin.users"))
    set_active(user, True)
    log_action(
        "user.activate",
        target_type="user",
        target_id=user.id,
        details={"email": user.email, "role": user.role},
    )
    db.session.commit()
    flash(f"User '{user.full_name}' activated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@admin_required
def deactivate_user(user_id: int):
    bad = _require_csrf_or_redirect(url_for("admin.users"))
    if bad:
        return bad
    user = find_user(user_id)
    if not user:
        abort(404)
    if user.id == session.get("user_id"):
        flash("Administrators cannot deactivate their own account.", "error")
        return redirect(url_for("admin.users"))
    if user.role == "admin" and count_admins() <= 1:
        flash("Cannot deactivate the only administrator account.", "error")
        return redirect(url_for("admin.users"))
    set_active(user, False)
    log_action(
        "user.deactivate",
        target_type="user",
        target_id=user.id,
        details={"email": user.email, "role": user.role},
    )
    db.session.commit()
    flash(f"User '{user.full_name}' deactivated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def reset_user_password(user_id: int):
    bad = _require_csrf_or_redirect(url_for("admin.users"))
    if bad:
        return bad
    user = find_user(user_id)
    if not user:
        abort(404)
    new_password = secrets.token_urlsafe(9)
    user.password_hash = generate_password_hash(new_password)
    log_action(
        "user.password_reset_by_admin",
        target_type="user",
        target_id=user.id,
        details={"email": user.email},
    )
    db.session.commit()
    flash(
        f"Temporary password for {user.full_name}: {new_password} (share securely).",
        "success",
    )
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id: int):
    bad = _require_csrf_or_redirect(url_for("admin.users"))
    if bad:
        return bad
    user = find_user(user_id)
    if not user:
        abort(404)
    if user.id == session.get("user_id"):
        flash("Administrators cannot delete their own account.", "error")
        return redirect(url_for("admin.users"))
    if user.role == "admin" and count_admins() <= 1:
        flash("Cannot delete the only administrator account.", "error")
        return redirect(url_for("admin.users"))
    details = {"email": user.email, "role": user.role, "name": user.full_name}
    delete_user_cascade(user)
    log_action("user.delete", target_type="user", target_id=user_id, details=details)
    db.session.commit()
    flash("User removed permanently.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/modules")
@admin_required
def modules():
    rows = Module.query.order_by(Module.display_order.asc()).all()
    return render_template("admin/modules.html", modules=rows)


@admin_bp.route("/modules/new", methods=["GET", "POST"])
@admin_required
def module_create():
    if request.method == "POST":
        bad = _require_csrf_or_redirect(url_for("admin.module_create"))
        if bad:
            return bad
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        route = (request.form.get("route") or "").strip()
        try:
            display_order = int(request.form.get("display_order") or 1)
        except (TypeError, ValueError):
            display_order = 1
        err = (
            validate_text_field(name, "Name", min_len=2, max_len=120)
            or validate_text_field(description, "Description", min_len=2, max_len=1000)
            or validate_text_field(route, "Route", min_len=1, max_len=120)
        )
        if err:
            flash(err, "error")
            return render_template(
                "admin/module_form.html",
                mode="create",
                module=None,
                form={
                    "name": name,
                    "description": description,
                    "route": route,
                    "display_order": display_order,
                },
            )
        if not route.startswith("/"):
            flash("Route must start with '/'.", "error")
            return render_template(
                "admin/module_form.html",
                mode="create",
                module=None,
                form={
                    "name": name,
                    "description": description,
                    "route": route,
                    "display_order": display_order,
                },
            )
        if Module.query.filter(func.lower(Module.name) == name.lower()).first():
            flash("A module with that name already exists.", "error")
            return render_template(
                "admin/module_form.html",
                mode="create",
                module=None,
                form={
                    "name": name,
                    "description": description,
                    "route": route,
                    "display_order": display_order,
                },
            )
        module = Module(
            name=name,
            description=description,
            route=route,
            display_order=display_order,
        )
        db.session.add(module)
        db.session.flush()
        log_action(
            "module.create",
            target_type="module",
            target_id=module.id,
            details={"name": name, "route": route},
        )
        db.session.commit()
        flash("Module created.", "success")
        return redirect(url_for("admin.modules"))

    return render_template("admin/module_form.html", mode="create", module=None, form=None)


@admin_bp.route("/modules/<int:module_id>/edit", methods=["GET", "POST"])
@admin_required
def module_edit(module_id: int):
    module = db.session.get(Module, module_id)
    if not module:
        abort(404)
    if request.method == "POST":
        bad = _require_csrf_or_redirect(url_for("admin.module_edit", module_id=module_id))
        if bad:
            return bad
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        route = (request.form.get("route") or "").strip()
        try:
            display_order = int(request.form.get("display_order") or 1)
        except (TypeError, ValueError):
            display_order = module.display_order
        err = (
            validate_text_field(name, "Name", min_len=2, max_len=120)
            or validate_text_field(description, "Description", min_len=2, max_len=1000)
            or validate_text_field(route, "Route", min_len=1, max_len=120)
        )
        if err:
            flash(err, "error")
            return render_template("admin/module_form.html", mode="edit", module=module, form=None)
        if not route.startswith("/"):
            flash("Route must start with '/'.", "error")
            return render_template("admin/module_form.html", mode="edit", module=module, form=None)
        clash = (
            Module.query.filter(func.lower(Module.name) == name.lower())
            .filter(Module.id != module.id)
            .first()
        )
        if clash:
            flash("Another module already uses that name.", "error")
            return render_template("admin/module_form.html", mode="edit", module=module, form=None)
        module.name = name
        module.description = description
        module.route = route
        module.display_order = display_order
        log_action(
            "module.update",
            target_type="module",
            target_id=module.id,
            details={"name": name, "route": route, "display_order": display_order},
        )
        db.session.commit()
        flash("Module updated.", "success")
        return redirect(url_for("admin.modules"))
    return render_template("admin/module_form.html", mode="edit", module=module, form=None)


@admin_bp.route("/modules/<int:module_id>/delete", methods=["POST"])
@admin_required
def module_delete(module_id: int):
    bad = _require_csrf_or_redirect(url_for("admin.modules"))
    if bad:
        return bad
    module = db.session.get(Module, module_id)
    if not module:
        abort(404)
    details = {"name": module.name, "route": module.route}
    TheoryContent.query.filter_by(module_id=module.id).delete(synchronize_session=False)
    db.session.delete(module)
    log_action("module.delete", target_type="module", target_id=module_id, details=details)
    db.session.commit()
    flash("Module removed.", "success")
    return redirect(url_for("admin.modules"))


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings_view():
    if request.method == "POST":
        bad = _require_csrf_or_redirect(url_for("admin.settings_view"))
        if bad:
            return bad
        system_name = (request.form.get("system_name") or "").strip()
        maintenance_mode = "1" if request.form.get("maintenance_mode") == "on" else "0"
        try:
            min_pwd_len = int(request.form.get("min_password_length") or 8)
        except (TypeError, ValueError):
            min_pwd_len = 8
        try:
            min_score = int(request.form.get("min_completion_score") or 70)
        except (TypeError, ValueError):
            min_score = 70

        name_err = validate_text_field(system_name, "System name", min_len=2, max_len=100)
        if name_err:
            flash(name_err, "error")
            return redirect(url_for("admin.settings_view"))
        if not 6 <= min_pwd_len <= 64:
            flash("Minimum password length must be between 6 and 64.", "error")
            return redirect(url_for("admin.settings_view"))
        if not 0 <= min_score <= 100:
            flash("Minimum completion score must be between 0 and 100.", "error")
            return redirect(url_for("admin.settings_view"))

        actor_id = session.get("user_id")
        set_setting("system_name", system_name, updated_by=actor_id)
        set_setting("maintenance_mode", maintenance_mode, updated_by=actor_id)
        set_setting("min_password_length", str(min_pwd_len), updated_by=actor_id)
        set_setting("min_completion_score", str(min_score), updated_by=actor_id)
        log_action(
            "settings.update",
            target_type="settings",
            details={
                "system_name": system_name,
                "maintenance_mode": maintenance_mode,
                "min_password_length": min_pwd_len,
                "min_completion_score": min_score,
            },
        )
        db.session.commit()
        flash("System settings updated.", "success")
        return redirect(url_for("admin.settings_view"))

    return render_template(
        "admin/settings.html",
        settings=all_settings(),
        defaults=DEFAULT_SETTINGS,
    )


@admin_bp.route("/audit")
@admin_required
def audit():
    page = max(1, int(request.args.get("page", 1) or 1))
    search = (request.args.get("q") or "").strip()
    action_filter = (request.args.get("action") or "").strip()
    user_filter = (request.args.get("user") or "").strip()
    start_date = (request.args.get("start") or "").strip()
    end_date = (request.args.get("end") or "").strip()
    paged = list_audit_logs(
        page=page,
        per_page=25,
        search=search,
        action_filter=action_filter,
        user_filter=user_filter,
        start_date=start_date or None,
        end_date=end_date or None,
    )
    return render_template(
        "admin/audit.html",
        paged=paged,
        search=search,
        action_filter=action_filter,
        user_filter=user_filter,
        start_date=start_date,
        end_date=end_date,
    )


@admin_bp.route("/reports")
@admin_required
def reports():
    return render_template(
        "admin/reports.html",
        report_labels=REPORT_LABELS,
    )


@admin_bp.route("/reports/<report_key>.csv")
@admin_required
def reports_download(report_key: str):
    builder = REPORT_BUILDERS.get(report_key)
    if not builder:
        abort(404)
    start = (request.args.get("start") or "").strip() or None
    end = (request.args.get("end") or "").strip() or None
    _, blob = builder(start, end)
    log_action(
        "report.download",
        target_type="report",
        details={"report": report_key, "start": start, "end": end},
    )
    db.session.commit()
    filename = f"ante_{report_key}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(
        BytesIO(blob),
        mimetype="text/csv; charset=utf-8",
        as_attachment=True,
        download_name=filename,
    )
