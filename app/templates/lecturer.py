from flask import Blueprint, render_template, redirect, url_for, session, request, flash

lecturer_bp = Blueprint("lecturer", __name__, url_prefix="/lecturer")


def lecturer_required():
    return session.get("role") == "lecturer" or session.get("demo_mode") is True


@lecturer_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session and not session.get("demo_mode"):
        return redirect(url_for("auth.login"))

    if not lecturer_required():
        return "Student access required", 403

    return render_template("lecturer_dashboard.html")


@lecturer_bp.route("/questions")
def question_bank():
    if "user_id" not in session and not session.get("demo_mode"):
        return redirect(url_for("auth.login"))

    if not lecturer_required():
        return "Student access required", 403

    return render_template("lecturer_questions.html")


@lecturer_bp.route("/questions/create", methods=["GET", "POST"])
def create_question():
    if "user_id" not in session and not session.get("demo_mode"):
        return redirect(url_for("auth.login"))

    if not lecturer_required():
        return "Student access required", 403

    if request.method == "POST":
        flash("Question created successfully", "success")
        return redirect(url_for("lecturer.question_bank"))

    return render_template("lecturer_question_form.html")


@lecturer_bp.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
def edit_question(question_id):
    if "user_id" not in session and not session.get("demo_mode"):
        return redirect(url_for("auth.login"))

    if not lecturer_required():
        return "Student access required", 403

    if request.method == "POST":
        flash("Question updated successfully", "success")
        return redirect(url_for("lecturer.question_bank"))

    return render_template("lecturer_question_form.html", question_id=question_id)


@lecturer_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
def delete_question(question_id):
    if "user_id" not in session and not session.get("demo_mode"):
        return redirect(url_for("auth.login"))

    if not lecturer_required():
        return "Student access required", 403

    flash("Question deleted successfully", "success")
    return redirect(url_for("lecturer.question_bank"))
