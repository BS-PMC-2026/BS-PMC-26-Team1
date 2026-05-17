from flask import Blueprint, render_template, redirect, url_for, session, request, flash

lecturer_bp = Blueprint("lecturer", __name__, url_prefix="/lecturer")


def is_authenticated():
    """
    Check if the user is logged in or demo mode is active.
    """
    return "user_id" in session or session.get("demo_mode") is True


def lecturer_required():
    """
    Allow access only for lecturer users or demo mode.
    Supports both 'lecturer' and 'teacher' role names.
    """
    role = session.get("role", "").lower()
    return role in ["lecturer", "teacher"] or session.get("demo_mode") is True


def redirect_to_login():
    """
    Redirect to login page safely.
    If auth.login endpoint does not exist, fallback to /login.
    """
    try:
        return redirect(url_for("auth.login"))
    except Exception:
        return redirect("/login")


@lecturer_bp.route("/")
def lecturer_home():
    """
    Redirect base lecturer route to lecturer dashboard.
    """
    return redirect(url_for("lecturer.dashboard"))


@lecturer_bp.route("/dashboard")
def dashboard():
    if not is_authenticated():
        return redirect_to_login()

    if not lecturer_required():
        return "Student access required", 403

    return render_template("lecturer_dashboard.html")


@lecturer_bp.route("/questions")
def question_bank():
    if not is_authenticated():
        return redirect_to_login()

    if not lecturer_required():
        return "Student access required", 403

    return render_template("lecturer_questions.html")


@lecturer_bp.route("/questions/create", methods=["GET", "POST"])
def create_question():
    if not is_authenticated():
        return redirect_to_login()

    if not lecturer_required():
        return "Student access required", 403

    if request.method == "POST":
        flash("Question created successfully", "success")
        return redirect(url_for("lecturer.question_bank"))

    return render_template("lecturer_question_form.html")


@lecturer_bp.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
def edit_question(question_id):
    if not is_authenticated():
        return redirect_to_login()

    if not lecturer_required():
        return "Student access required", 403

    if request.method == "POST":
        flash("Question updated successfully", "success")
        return redirect(url_for("lecturer.question_bank"))

    return render_template(
        "lecturer_question_form.html",
        question_id=question_id
    )


@lecturer_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
def delete_question(question_id):
    if not is_authenticated():
        return redirect_to_login()

    if not lecturer_required():
        return "Student access required", 403

    flash("Question deleted successfully", "success")
    return redirect(url_for("lecturer.question_bank"))
