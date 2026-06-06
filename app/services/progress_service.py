from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from app.models import ExerciseAttempt, Module, ModuleProgress, ProgressRecord, Question, db


@dataclass
class ProgressStats:
    modules_total: int
    modules_completed: int
    modules_remaining: int
    module_percent: int
    total_attempts: int
    correct_answers: int
    success_rate: int
    exercises_total: int
    exercises_answered: int
    exercises_correct: int


def calculate_success_rate(correct_answers: int, total_attempts: int) -> int:
    if total_attempts <= 0:
        return 0
    return int((correct_answers / total_attempts) * 100)


def get_or_create_progress_record(user_id: int) -> ProgressRecord:
    record = ProgressRecord.query.filter_by(user_id=user_id).first()
    if not record:
        record = ProgressRecord(user_id=user_id)
        db.session.add(record)
        db.session.flush()
    return record


def _resolve_record_field(module_name: str) -> Optional[str]:
    mapping = {
        "intro": "intro_completed",
        "pipeline": "pipeline_viewed",
        "exercise": "exercise_completed",
    }
    return mapping.get(module_name.lower())


def _get_or_create_module_progress(user_id: int, module_id: int) -> ModuleProgress:
    row = ModuleProgress.query.filter_by(user_id=user_id, module_id=module_id).first()
    if not row:
        row = ModuleProgress(
            user_id=user_id,
            module_id=module_id,
            completed=False,
            progress_percentage=0,
        )
        db.session.add(row)
        db.session.flush()
    return row


def mark_module_completed(user_id: int, module_key: str) -> ProgressRecord:
    record = get_or_create_progress_record(user_id)
    module = Module.query.filter(Module.name.ilike(module_key)).first()
    if module:
        module_row = _get_or_create_module_progress(user_id, module.id)
        module_row.completed = True
        module_row.progress_percentage = 100

    field = _resolve_record_field(module_key)
    if field:
        setattr(record, field, True)

    return record


def update_module_progress_percent(user_id: int, module_name: str, percent: int, completed: bool = False) -> None:
    module = Module.query.filter(Module.name.ilike(module_name)).first()
    if not module:
        return
    progress = _get_or_create_module_progress(user_id, module.id)
    progress.progress_percentage = max(0, min(100, int(percent)))
    if completed or progress.progress_percentage >= 100:
        progress.completed = True


def record_exercise_attempt(user_id: int, question_id: int, is_correct: bool) -> ProgressRecord:
    record = get_or_create_progress_record(user_id)
    record.total_attempts += 1
    if is_correct:
        record.correct_answers_count += 1

    all_exercise_questions = (
        Question.query.join(Module, Question.module_id == Module.id)
        .filter(Module.name.ilike("exercise"), Question.is_active.is_(True))
        .all()
    )
    total_questions = len(all_exercise_questions)
    completed_question_ids = {
        row[0]
        for row in db.session.query(db.func.distinct(ExerciseAttempt.question_id))
        .filter(
            ExerciseAttempt.user_id == user_id,
            ExerciseAttempt.is_correct.is_(True),
            ExerciseAttempt.question_id.isnot(None),
        )
        .all()
        if row and row[0] is not None
    }
    if is_correct:
        completed_question_ids.add(question_id)

    exercise_percent = int((len(completed_question_ids) / total_questions) * 100) if total_questions else 0
    try:
        from app.services.settings_service import get_setting_int

        completion_threshold = get_setting_int("min_completion_score", 70)
    except Exception:
        completion_threshold = 70
    is_exercise_complete = total_questions > 0 and exercise_percent >= completion_threshold
    update_module_progress_percent(user_id, "Exercise", exercise_percent, completed=is_exercise_complete)

    record.exercise_completed = is_exercise_complete
    record.score = calculate_success_rate(record.correct_answers_count, record.total_attempts)
    return record


def build_module_states(record: Optional[ProgressRecord], user_id: Optional[int] = None) -> List[Dict]:
    modules = Module.query.order_by(Module.display_order.asc()).all()
    module_progress_map = {}
    if user_id:
        for row in ModuleProgress.query.filter_by(user_id=user_id).all():
            module_progress_map[row.module_id] = row

    states = []
    current_marked = False
    for module in modules:
        row = module_progress_map.get(module.id)
        completed = bool(row.completed) if row else False
        progress_percentage = row.progress_percentage if row else 0
        is_current = False
        if not completed and not current_marked:
            is_current = True
            current_marked = True
        states.append(
            {
                "order": module.display_order,
                "key": module.name.lower(),
                "title": module.name,
                "description": module.description,
                "route": module.route,
                "completed": completed,
                "is_current": is_current,
                "progress_percentage": progress_percentage,
            }
        )
    return states


def build_progress_stats(record: Optional[ProgressRecord], user_id: int) -> ProgressStats:
    module_states = build_module_states(record, user_id=user_id)
    modules_total = len(module_states)
    modules_completed = sum(1 for item in module_states if item["completed"])
    modules_remaining = modules_total - modules_completed
    module_percent = int((modules_completed / modules_total) * 100) if modules_total else 0

    total_attempts = record.total_attempts if record else 0
    correct_answers = record.correct_answers_count if record else 0
    success_rate = calculate_success_rate(correct_answers, total_attempts)

    exercise_questions = (
        Question.query.join(Module, Question.module_id == Module.id)
        .filter(Module.name.ilike("exercise"), Question.is_active.is_(True))
        .all()
    )
    exercise_question_ids = {q.id for q in exercise_questions}
    answered_question_ids = {
        row[0]
        for row in db.session.query(db.func.distinct(ExerciseAttempt.question_id))
        .filter(
            ExerciseAttempt.user_id == user_id,
            ExerciseAttempt.question_id.isnot(None),
        )
        .all()
        if row and row[0] is not None and row[0] in exercise_question_ids
    }
    correct_question_ids = {
        row[0]
        for row in db.session.query(db.func.distinct(ExerciseAttempt.question_id))
        .filter(
            ExerciseAttempt.user_id == user_id,
            ExerciseAttempt.is_correct.is_(True),
            ExerciseAttempt.question_id.isnot(None),
        )
        .all()
        if row and row[0] is not None and row[0] in exercise_question_ids
    }

    return ProgressStats(
        modules_total=modules_total,
        modules_completed=modules_completed,
        modules_remaining=modules_remaining,
        module_percent=module_percent,
        total_attempts=total_attempts,
        correct_answers=correct_answers,
        success_rate=success_rate,
        exercises_total=len(exercise_question_ids),
        exercises_answered=len(answered_question_ids),
        exercises_correct=len(correct_question_ids),
    )


def get_demo_progress_context() -> Dict:
    module_states = []
    modules = Module.query.order_by(Module.display_order.asc()).all()
    if not modules:
        module_states = [
            {
                "order": 1,
                "key": "intro",
                "title": "Intro",
                "description": "CI/CD fundamentals and practical benefits.",
                "route": "/intro",
                "completed": True,
                "is_current": False,
                "progress_percentage": 100,
            },
            {
                "order": 2,
                "key": "pipeline",
                "title": "Pipeline",
                "description": "Interactive CI/CD pipeline stages.",
                "route": "/pipeline",
                "completed": True,
                "is_current": False,
                "progress_percentage": 100,
            },
            {
                "order": 3,
                "key": "exercise",
                "title": "Exercise",
                "description": "Hands-on mixed question practice.",
                "route": "/exercise",
                "completed": True,
                "is_current": False,
                "progress_percentage": 100,
            },
        ]
    else:
        for module in modules:
            module_states.append(
                {
                    "order": module.display_order,
                    "key": module.name.lower(),
                    "title": module.name,
                    "description": module.description,
                    "route": module.route,
                    "completed": True,
                    "is_current": False,
                    "progress_percentage": 100,
                }
            )

    return {
        "module_states": module_states,
        "stats": ProgressStats(
            modules_total=len(module_states),
            modules_completed=len(module_states),
            modules_remaining=0,
            module_percent=100,
            total_attempts=8,
            correct_answers=7,
            success_rate=88,
            exercises_total=4,
            exercises_answered=4,
            exercises_correct=4,
        ),
    }
