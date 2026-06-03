from datetime import datetime, timedelta

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import LecturerProfile, StudentProfile, User, db
from app.services.audit_service import log_action
from app.services.live_export_service import export_users_live_snapshot
from app.services.security_service import (
    consume_password_reset_token,
    create_password_reset_token,
    is_account_locked,
    LOCKOUT_MINUTES,
    mark_token_used,
    record_login_attempt,
    validate_csrf_token,
    validate_email,
    validate_password,
    validate_text_field,
)
from app.services.state_service import sync_session_from_learning_state

auth_bp = Blueprint("auth", __name__)


def _csrf_ok() -> bool:
    return validate_csrf_token(request.form.get("csrf_token"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not _csrf_ok():
            flash("Security check failed. Please retry the form.", "error")
            return redirect(url_for("auth.register"))

        username = (request.form.get("username") or "").strip()
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""
        role = (request.form.get("role") or "").strip()

        if not username:
            username = email.split("@")[0] if email else ""

        validation_error = (
            validate_text_field(username, "Username", min_len=3, max_len=80)
            or validate_text_field(full_name, "Full name", min_len=2, max_len=100)
            or validate_email(email)
        )
        if validation_error:
            flash(validation_error, "error")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.register"))

        pwd_error = validate_password(password)
        if pwd_error:
            flash(pwd_error, "error")
            return redirect(url_for("auth.register"))

        if role not in {"student", "lecturer"}:
            flash("Role must be either student or lecturer.", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email address already exists.", "error")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            full_name=full_name,
            email=email,
            password_hash=hashed_password,
            role=role,
        )
        db.session.add(new_user)
        db.session.flush()

        if role == "student":
            db.session.add(StudentProfile(user_id=new_user.id))
        elif role == "lecturer":
            db.session.add(LecturerProfile(user_id=new_user.id))

        log_action(
            "user.register",
            user_id=new_user.id,
            target_type="user",
            target_id=new_user.id,
            details={"role": role, "email": email},
        )
        db.session.commit()
        export_users_live_snapshot()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not _csrf_ok():
            flash("Security check failed. Please retry the form.", "error")
            return redirect(url_for("auth.login"))

        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        locked, unlock_at = is_account_locked(email)
        if locked:
            remaining_min = max(
                1, int((unlock_at - datetime.utcnow()).total_seconds() // 60) + 1
            )
            log_action(
                "auth.login_locked",
                target_type="user_email",
                details={"email": email, "remaining_minutes": remaining_min},
            )
            db.session.commit()
            flash(
                f"Account temporarily locked due to repeated failed logins. "
                f"Try again in about {remaining_min} minute(s).",
                "error",
            )
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()
        if user and not user.is_active:
            record_login_attempt(email, success=False)
            log_action(
                "auth.login_inactive",
                user_id=user.id,
                target_type="user",
                target_id=user.id,
                details={"email": email},
            )
            db.session.commit()
            flash("This account has been deactivated. Contact an administrator.", "error")
            return redirect(url_for("auth.login"))

        if user and check_password_hash(user.password_hash, password):
            record_login_attempt(email, success=True)
            log_action(
                "auth.login_success",
                user_id=user.id,
                target_type="user",
                target_id=user.id,
                details={"role": user.role},
            )
            session.clear()
            session.permanent = True
            session["user_id"] = user.id
            session["role"] = user.role
            session["user_name"] = user.full_name
            session["demo_mode"] = False
            session["login_at"] = datetime.utcnow().isoformat()
            sync_session_from_learning_state(user.id)
            db.session.commit()
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            if user.role == "lecturer":
                return redirect(url_for("lecturer.lecturer_dashboard"))
            return redirect(url_for("main.home"))

        record_login_attempt(email, success=False)
        log_action(
            "auth.login_failure",
            user_id=user.id if user else None,
            target_type="user_email",
            details={"email": email},
        )
        db.session.commit()
        flash("Login failed. Check your email and password.", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        log_action("auth.logout", user_id=user_id, target_type="user", target_id=user_id)
        db.session.commit()
    session.clear()
    return redirect(url_for("main.home"))


@auth_bp.route("/demo")
def demo():
    session.clear()
    session["user_id"] = 0
    session["role"] = "lecturer"
    session["user_name"] = "Demo Lecturer"
    session["demo_mode"] = True
    flash("Enabled Lecturer Demo Mode.", "success")
    return redirect(url_for("main.demo_view"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        if not _csrf_ok():
            flash("Security check failed. Please retry the form.", "error")
            return redirect(url_for("auth.forgot_password"))

        email = (request.form.get("email") or "").strip().lower()
        email_error = validate_email(email)
        if email_error:
            flash(email_error, "error")
            return redirect(url_for("auth.forgot_password"))

        user = User.query.filter_by(email=email).first()
        if user and user.is_active:
            token_row = create_password_reset_token(user)
            reset_url = url_for(
                "auth.reset_password", token=token_row.token, _external=True
            )
            current_app.logger.info("Password reset link for %s: %s", email, reset_url)
            print(f"[ANTE] Password reset link for {email}: {reset_url}")
            log_action(
                "auth.password_reset_requested",
                user_id=user.id,
                target_type="user",
                target_id=user.id,
            )
        db.session.commit()
        flash(
            "If the email is registered, a reset link has been issued. "
            "Check your inbox (and the server console in development).",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    row = consume_password_reset_token(token)
    if not row:
        flash("Reset link is invalid or has expired. Request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        if not _csrf_ok():
            flash("Security check failed. Please retry the form.", "error")
            return redirect(url_for("auth.reset_password", token=token))

        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.reset_password", token=token))

        pwd_error = validate_password(password)
        if pwd_error:
            flash(pwd_error, "error")
            return redirect(url_for("auth.reset_password", token=token))

        user = db.session.get(User, row.user_id)
        if not user:
            flash("Account not found. Contact an administrator.", "error")
            return redirect(url_for("auth.login"))

        user.password_hash = generate_password_hash(password)
        mark_token_used(row)
        log_action(
            "auth.password_reset_completed",
            user_id=user.id,
            target_type="user",
            target_id=user.id,
        )
        db.session.commit()
        flash("Password updated successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token)
