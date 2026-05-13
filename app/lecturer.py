import json

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.models import Module, Question, User, db
from app.services.analytics_service import get_lecturer_dashboard_metrics
from app.services.authz import lecturer_required
from app.services.question_service import list_question_bank, parse_options_input
from app.services.theory_service import get_or_create_theory_content
from app.seed import QuestionType

lecturer_bp = Blueprint("lecturer", __name__)


def _demo_write_block():
    if session.get("demo_mode") and request.method == "POST":
        flash("Demo mode is read-only. Disable demo mode to save changes.", "error")
        return redirect(url_for("main.demo_view"))
    return None


def _parse_module_id(raw_value: str) -> int:
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return 0


def _validate_test_cases_json(raw_test_cases: str) -> bool:
    if not raw_test_cases.strip():
        return True
    try:
        parsed = json.loads(raw_test_cases)
        return isinstance(parsed, list)
    except json.JSONDecodeError:
        return False


@lecturer_bp.route("/lecturer/dashboard")
@lecturer_required
def lecturer_dashboard():
    metrics = get_lecturer_dashboard_metrics()
    return render_template("lecturer_dashboard.html", metrics=metrics)


@lecturer_bp.route("/lecturer/questions")
@lecturer_required
def lecturer_questions():
    questions = list_question_bank(include_inactive=True)
    modules = Module.query.order_by(Module.display_order.asc()).all()
    modules_by_id = {m.id: m for m in modules}
    return render_template(
        "lecturer_questions.html",
        questions=questions,
        modules_by_id=modules_by_id,
    )


@lecturer_bp.route("/lecturer/questions/new", methods=["GET", "POST"])
@lecturer_required
def lecturer_question_create():
    blocked = _demo_write_block()
    if blocked:
        return blocked

    modules = Module.query.order_by(Module.display_order.asc()).all()
    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        question_type = request.form.get("question_type", QuestionType.MCQ.value)
        correct_answer = request.form.get("correct_answer", "").strip()
        explanation = request.form.get("explanation", "").strip()
        difficulty = request.form.get("difficulty", "medium")
        module_id = _parse_module_id(request.form.get("module_id", "0"))
        starter_code = request.form.get("starter_code", "")
        raw_options = request.form.get("options", "")
        raw_test_cases = request.form.get("test_cases_json", "")
        module_row = Module.query.get(module_id)

        if not question_text or not correct_answer or not explanation or module_id <= 0 or not module_row:
            flash("Question text, answer, explanation, and module are required.", "error")
            return render_template(
                "lecturer_question_form.html",
                mode="create",
                modules=modules,
                question=None,
            )

        if question_type not in {QuestionType.MCQ.value, QuestionType.CODE.value, QuestionType.OPEN.value}:
            flash("Question type is invalid.", "error")
            return render_template(
                "lecturer_question_form.html",
                mode="create",
                modules=modules,
                question=None,
            )

        if question_type == QuestionType.CODE.value and not _validate_test_cases_json(raw_test_cases):
            flash("Test Cases JSON must be a valid JSON list.", "error")
            return render_template(
                "lecturer_question_form.html",
                mode="create",
                modules=modules,
                question=None,
            )

        if question_type == QuestionType.MCQ.value:
            options_json = parse_options_input(raw_options)
            if options_json == "[]":
                flash("MCQ questions require at least one option.", "error")
                return render_template(
                    "lecturer_question_form.html",
                    mode="create",
                    modules=modules,
                    question=None,
                )
        else:
            options_json = "[]"

        question = Question(
            question_text=question_text,
            question_type=question_type,
            options_json=options_json,
            correct_answer=correct_answer,
            explanation=explanation,
            difficulty=difficulty,
            module_id=module_id,
            starter_code=starter_code if question_type == QuestionType.CODE.value else None,
            test_cases_json=raw_test_cases if question_type == QuestionType.CODE.value and raw_test_cases else None,
            created_by=session.get("user_id"),
            is_active=True,
        )
        db.session.add(question)
        db.session.commit()
        flash("Question created successfully.", "success")
        return redirect(url_for("lecturer.lecturer_questions"))

    return render_template(
        "lecturer_question_form.html",
        mode="create",
        modules=modules,
        question=None,
    )


@lecturer_bp.route("/lecturer/questions/<int:question_id>/edit", methods=["GET", "POST"])
@lecturer_required
def lecturer_question_edit(question_id: int):
    blocked = _demo_write_block()
    if blocked:
        return blocked

    question = Question.query.get_or_404(question_id)
    modules = Module.query.order_by(Module.display_order.asc()).all()
    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        question_type = request.form.get("question_type", QuestionType.MCQ.value)
        correct_answer = request.form.get("correct_answer", "").strip()
        explanation = request.form.get("explanation", "").strip()
        question.difficulty = request.form.get("difficulty", "medium")
        module_id = _parse_module_id(request.form.get("module_id", question.module_id))
        module_row = Module.query.get(module_id)

        if not question_text or not correct_answer or not explanation or not module_row:
            flash("Question text, answer, explanation, and valid module are required.", "error")
            return render_template(
                "lecturer_question_form.html",
                mode="edit",
                modules=modules,
                question=question,
            )
        if question_type not in {QuestionType.MCQ.value, QuestionType.CODE.value, QuestionType.OPEN.value}:
            flash("Question type is invalid.", "error")
            return render_template(
                "lecturer_question_form.html",
                mode="edit",
                modules=modules,
                question=question,
            )

        question.question_text = question_text
        question.question_type = question_type
        question.correct_answer = correct_answer
        question.explanation = explanation
        question.module_id = module_id

        raw_options = request.form.get("options", "")
        if question.question_type == QuestionType.MCQ.value:
            question.options_json = parse_options_input(raw_options)
            if question.options_json == "[]":
                flash("MCQ questions require at least one option.", "error")
                return render_template(
                    "lecturer_question_form.html",
                    mode="edit",
                    modules=modules,
                    question=question,
                )
        else:
            question.options_json = "[]"

        if question.question_type == QuestionType.CODE.value:
            raw_test_cases = request.form.get("test_cases_json", "")
            if not _validate_test_cases_json(raw_test_cases):
                flash("Test Cases JSON must be a valid JSON list.", "error")
                return render_template(
                    "lecturer_question_form.html",
                    mode="edit",
                    modules=modules,
                    question=question,
                )
            question.starter_code = request.form.get("starter_code", "")
            question.test_cases_json = raw_test_cases
        else:
            question.starter_code = None
            question.test_cases_json = None

        question.is_active = request.form.get("is_active") == "on"
        db.session.commit()
        flash("Question updated successfully.", "success")
        return redirect(url_for("lecturer.lecturer_questions"))

    return render_template(
        "lecturer_question_form.html",
        mode="edit",
        modules=modules,
        question=question,
    )


@lecturer_bp.route("/lecturer/questions/<int:question_id>/delete", methods=["POST"])
@lecturer_required
def lecturer_question_delete(question_id: int):
    blocked = _demo_write_block()
    if blocked:
        return blocked

    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted.", "success")
    return redirect(url_for("lecturer.lecturer_questions"))


@lecturer_bp.route("/lecturer/theory")
@lecturer_required
def lecturer_theory():
    modules = Module.query.filter(Module.name.in_(["Intro", "Pipeline"])).order_by(Module.display_order.asc()).all()
    theory_rows = []
    for module in modules:
        theory_rows.append({"module": module, "content": get_or_create_theory_content(module.name)})
    db.session.commit()
    return render_template("lecturer_theory.html", theory_rows=theory_rows)


@lecturer_bp.route("/lecturer/theory/<module_name>", methods=["GET", "POST"])
@lecturer_required
def lecturer_theory_edit(module_name: str):
    module = Module.query.filter(Module.name.ilike(module_name)).first_or_404()
    if module.name.lower() not in {"intro", "pipeline"}:
        flash("Theory management is available for Intro and Pipeline modules only.", "error")
        return redirect(url_for("lecturer.lecturer_theory"))

    blocked = _demo_write_block()
    if blocked:
        return blocked

    content = get_or_create_theory_content(module.name)
    if request.method == "POST":
        headline = request.form.get("headline", "").strip()
        explanation = request.form.get("explanation", "").strip()
        examples = request.form.get("examples", "").strip()
        if not headline or not explanation or not examples:
            flash("Headline, explanation, and examples are required.", "error")
            return render_template("lecturer_theory_form.html", module=module, content=content)

        content.headline = headline
        content.explanation = explanation
        content.examples = examples
        content.updated_by = session.get("user_id")
        db.session.commit()
        flash("Theory content updated successfully.", "success")
        return redirect(url_for("lecturer.lecturer_theory"))

    db.session.commit()
    return render_template("lecturer_theory_form.html", module=module, content=content)
