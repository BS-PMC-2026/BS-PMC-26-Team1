from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models import ExerciseAttempt, Question, db
from app.seed import QuestionType
from app.services.analytics_service import refresh_user_analytics
from app.services.authz import student_required
from app.services.code_runner_service import run_student_code
from app.services.feedback import check_answer
from app.services.progress_service import (
    mark_module_completed,
    record_exercise_attempt,
    update_module_progress_percent,
)
from app.services.question_service import (
    get_or_create_question_order,
    get_question_by_id,
    mark_question_seen,
    serialize_question,
)
from app.services.state_service import persist_learning_state
from app.services.unit_test_service import run_student_unit_test

exercise_bp = Blueprint("exercise", __name__)


CODE_TYPES = {QuestionType.CODE.value}
QUIZ_TYPES = {QuestionType.MCQ.value, QuestionType.OPEN.value}


def _filter_order_by_track(order, track):
    """Return only the question ids that belong to the selected track."""
    if not track or track not in {"quiz", "code"}:
        return order
    keep = QUIZ_TYPES if track == "quiz" else CODE_TYPES
    filtered = []
    for qid in order:
        q = get_question_by_id(qid)
        if q and q.question_type in keep:
            filtered.append(qid)
    return filtered


@exercise_bp.route("/exercise", methods=["GET", "POST"])
@student_required
def exercise():
    user_id = session.get("user_id")
    demo_mode = bool(session.get("demo_mode"))

    track = (request.args.get("track") or "").lower()
    if track not in {"quiz", "code"}:
        track = ""

    feedback_result = None
    question_order = get_or_create_question_order()
    if not question_order:
        flash("No exercise questions available. Ask a lecturer to add questions.", "error")
        return redirect(url_for("main.home"))

    random_mode = request.args.get("random") == "1"
    active_order = question_order if random_mode else sorted(question_order)
    active_order = _filter_order_by_track(active_order, track)
    if not active_order:
        # The selected track has no questions of that type — show the picker page.
        return render_template(
            "exercise_hub.html",
            quiz_count=len(_filter_order_by_track(question_order, "quiz")),
            code_count=len(_filter_order_by_track(question_order, "code")),
            total_count=len(question_order),
            empty_track=track,
        )

    q_index = int(request.args.get("q", 0) or 0)
    if q_index < 0 or q_index >= len(active_order):
        q_index = 0
    current_question_obj = get_question_by_id(active_order[q_index])
    if not current_question_obj:
        flash("Question unavailable. Reloading question session.", "error")
        session.pop("exercise_question_order", None)
        session.pop("exercise_seen_ids", None)
        return redirect(url_for("exercise.exercise"))
    current_question = serialize_question(current_question_obj)
    if not demo_mode:
        persist_learning_state(user_id, current_module_name="Exercise", last_route="/exercise")

    last_attempt = None
    if not demo_mode:
        last_attempt = (
            ExerciseAttempt.query.filter_by(
                user_id=user_id, question_id=current_question["id"]
            )
            .order_by(ExerciseAttempt.submitted_at.desc())
            .first()
        )

    if request.method == "POST":
        action = request.form.get("action", "submit")

        # --- Unit-test phase for CODE questions -------------------------------
        if action == "submit_unit_test" and current_question["type"] == QuestionType.CODE.value:
            test_code = request.form.get("unit_test_code", "").strip()
            if not last_attempt or not last_attempt.is_correct:
                flash(
                    "You can only submit unit tests after your solution has passed.",
                    "error",
                )
                return redirect(
                    url_for("exercise.exercise", q=q_index, track=track or None)
                )
            ut_result = run_student_unit_test(
                solution_code=last_attempt.answer,
                test_code=test_code,
            )
            if not demo_mode:
                last_attempt.unit_test_code = test_code
                last_attempt.unit_test_passed = bool(ut_result.get("passed"))
                last_attempt.unit_test_output = ut_result.get("output_log", "")
                db.session.commit()
            feedback_result = {
                "stage": "unit_test",
                "is_correct": bool(ut_result.get("passed")),
                "status": "Unit tests passed" if ut_result.get("passed") else "Unit tests failed",
                "explanation": ut_result.get("output_log", ""),
                "assertions": ut_result.get("assertions", 0),
                "question_type": current_question["type"],
                "question_title": current_question["title"],
                "question_id": current_question["id"],
            }
            return render_template(
                "exercise.html",
                question=current_question,
                q_index=q_index,
                total_questions=len(active_order),
                feedback=feedback_result,
                random_mode=random_mode,
                track=track,
                last_attempt=last_attempt,
            )

        # --- Regular submit ---------------------------------------------------
        if current_question["type"] == QuestionType.MCQ.value:
            user_answer = request.form.get("answer", "")
        elif current_question["type"] == QuestionType.OPEN.value:
            user_answer = request.form.get("open_answer", "")
        else:
            user_answer = request.form.get("code_answer", "")

        feedback_result = check_answer(
            user_answer,
            expected_answer=current_question["expected_answer"],
            explanation=current_question.get("explanation", ""),
            question_type=current_question["type"],
            test_cases=current_question.get("test_cases") or None,
            language=current_question.get("language"),
        )
        feedback_result["stage"] = "solution"
        feedback_result["question_type"] = current_question["type"]
        feedback_result["question_title"] = current_question["title"]
        feedback_result["question_id"] = current_question["id"]

        mark_question_seen(current_question["id"])
        if not demo_mode:
            score = feedback_result.get("score", 100 if feedback_result["is_correct"] else 0)
            attempt = ExerciseAttempt(
                user_id=user_id,
                question_id=current_question["id"],
                answer=user_answer,
                submitted_output=feedback_result.get("raw_runner_output", ""),
                is_correct=feedback_result["is_correct"],
                feedback_text=feedback_result["status"] + " | " + feedback_result["explanation"],
                score=score,
            )
            db.session.add(attempt)
            db.session.flush()
            last_attempt = attempt
            record = record_exercise_attempt(
                user_id=user_id,
                question_id=current_question["id"],
                is_correct=feedback_result["is_correct"],
            )
            progress_percent = int(((q_index + 1) / len(active_order)) * 100)
            update_module_progress_percent(
                user_id, "Exercise", progress_percent, completed=record.exercise_completed
            )
            if record.exercise_completed:
                mark_module_completed(user_id, "exercise")
            refresh_user_analytics(user_id)
            persist_learning_state(user_id, current_module_name="Exercise", last_route="/exercise")
            db.session.commit()
    elif not demo_mode:
        db.session.commit()

    return render_template(
        "exercise.html",
        question=current_question,
        q_index=q_index,
        total_questions=len(active_order),
        feedback=feedback_result,
        random_mode=random_mode,
        track=track,
        last_attempt=last_attempt,
    )


@exercise_bp.route("/exercise/run", methods=["POST"])
def run_code():
    """
    Hooks into the Code Runner Sandbox returning local Python outputs safely.
    """
    user_id = session.get("user_id")
    if not user_id and not session.get("demo_mode"):
        return jsonify({"output": "Session missing. Please login."}), 401

    data = request.json or {}
    code = data.get("code", "")

    question_id = data.get("question_id")
    mock_test_cases = None
    language = data.get("language")
    if question_id:
        question = db.session.get(Question, question_id)
        if question:
            if question.code_test_cases:
                mock_test_cases = question.code_test_cases
            if language is None:
                language = question.language
    if not mock_test_cases:
        mock_test_cases = [
            {"inputs": [2, 3], "expected": 5},
            {"inputs": [-1, 1], "expected": 0},
        ]

    run_results = run_student_code(code, mock_test_cases, language=language)
    return jsonify({"output": run_results["output_log"]})


@exercise_bp.route("/exercise/preview-tests", methods=["POST"])
def preview_unit_test():
    """Live preview for the student's own unit-test draft."""
    user_id = session.get("user_id")
    if not user_id and not session.get("demo_mode"):
        return jsonify({"passed": False, "output": "Session missing."}), 401

    data = request.json or {}
    solution = data.get("solution_code", "")
    tests = data.get("test_code", "")
    result = run_student_unit_test(solution_code=solution, test_code=tests)
    return jsonify(
        {
            "passed": result.get("passed", False),
            "assertions": result.get("assertions", 0),
            "output": result.get("output_log", ""),
        }
    )
