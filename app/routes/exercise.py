from flask import Blueprint, render_template, request, session, flash, jsonify, redirect, url_for

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

exercise_bp = Blueprint('exercise', __name__)

@exercise_bp.route('/exercise', methods=['GET', 'POST'])
@student_required
def exercise():
    user_id = session.get('user_id')
    demo_mode = bool(session.get("demo_mode"))

    feedback_result = None
    question_order = get_or_create_question_order()
    if not question_order:
        flash("No exercise questions available. Ask a lecturer to add questions.", "error")
        return redirect(url_for("main.home"))

    random_mode = request.args.get("random") == "1"
    active_order = question_order if random_mode else sorted(question_order)

    q_index = int(request.args.get('q', 0) or 0)
    if q_index < 0 or q_index >= len(active_order):
        q_index = 0
    current_question_obj = get_question_by_id(active_order[q_index])
    if not current_question_obj:
        flash("Question unavailable. Reloading question session.", "error")
        session.pop("exercise_question_order", None)
        session.pop("exercise_seen_ids", None)
        return redirect(url_for("exercise.exercise"))
    current_question = serialize_question(current_question_obj)

    if request.method == 'POST':
        if current_question['type'] == QuestionType.MCQ.value:
            user_answer = request.form.get('answer', '')
        elif current_question['type'] == QuestionType.OPEN.value:
            user_answer = request.form.get('open_answer', '')
        else:
            user_answer = request.form.get('code_answer', '')

        feedback_result = check_answer(
            user_answer,
            expected_answer=current_question["expected_answer"],
            explanation=current_question.get("explanation", ""),
            question_type=current_question["type"],
            test_cases=current_question.get("test_cases") or None,
        )
        feedback_result["question_type"] = current_question["type"]
        feedback_result["question_title"] = current_question["title"]
        feedback_result["question_id"] = current_question["id"]

        mark_question_seen(current_question["id"])
        if not demo_mode:
            score = feedback_result.get("score", 100 if feedback_result["is_correct"] else 0)
            attempt = ExerciseAttempt(
                user_id=user_id,
                question_id=current_question['id'],
                answer=user_answer,
                submitted_output=feedback_result.get('raw_runner_output', ''),
                is_correct=feedback_result['is_correct'],
                feedback_text=feedback_result['status'] + " | " + feedback_result['explanation'],
                score=score,
            )
            db.session.add(attempt)
            record = record_exercise_attempt(
                user_id=user_id,
                question_id=current_question["id"],
                is_correct=feedback_result["is_correct"],
            )
            progress_percent = int(((q_index + 1) / len(active_order)) * 100)
            update_module_progress_percent(user_id, "Exercise", progress_percent, completed=record.exercise_completed)
            if record.exercise_completed:
                mark_module_completed(user_id, 'exercise')
            refresh_user_analytics(user_id)
            db.session.commit()

    return render_template(
        'exercise.html',
        question=current_question,
        q_index=q_index,
        total_questions=len(active_order),
        feedback=feedback_result,
        random_mode=random_mode,
    )

@exercise_bp.route('/exercise/run', methods=['POST'])
def run_code():
    """
    Hooks directly into the Code Runner Sandbox returning local Python outputs safely.
    """
    user_id = session.get("user_id")
    if not user_id and not session.get("demo_mode"):
        return jsonify({"output": "Session missing. Please login."}), 401

    data = request.json or {}
    code = data.get('code', '')

    question_id = data.get("question_id")
    mock_test_cases = None
    if question_id:
        question = Question.query.get(question_id)
        if question and question.code_test_cases:
            mock_test_cases = question.code_test_cases
    if not mock_test_cases:
        mock_test_cases = [
            {"inputs": [2, 3], "expected": 5},
            {"inputs": [-1, 1], "expected": 0},
        ]

    run_results = run_student_code(code, mock_test_cases)

    return jsonify({"output": run_results["output_log"]})
