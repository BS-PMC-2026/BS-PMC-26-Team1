import json
import random
from typing import Dict, List, Optional

from flask import session

from app.models import Module, Question, db
from app.seed import get_seed_questions


def list_question_bank(include_inactive: bool = True) -> List[Question]:
    query = Question.query.order_by(Question.created_at.desc())
    if not include_inactive:
        query = query.filter_by(is_active=True)
    return query.all()


def serialize_question(question: Question) -> Dict:
    seed_title_map = {row["id"]: row.get("title", "") for row in get_seed_questions()}
    return {
        "id": question.id,
        "type": question.question_type,
        "title": seed_title_map.get(question.id, f"Question {question.id}"),
        "content": question.question_text,
        "expected_answer": question.correct_answer,
        "options": question.options,
        "starter_code": question.starter_code or "",
        "explanation": question.explanation,
        "difficulty": question.difficulty,
        "module_id": question.module_id,
        "test_cases": question.code_test_cases,
    }


def get_question_by_id(question_id: int) -> Optional[Question]:
    return Question.query.get(question_id)


def get_exercise_questions() -> List[Question]:
    exercise_module = Module.query.filter(Module.name.ilike("Exercise")).first()
    if not exercise_module:
        return []
    return (
        Question.query.filter_by(module_id=exercise_module.id, is_active=True)
        .order_by(Question.id.asc())
        .all()
    )


def _session_question_order_key() -> str:
    return "exercise_question_order"


def _session_seen_key() -> str:
    return "exercise_seen_ids"


def initialize_question_order() -> List[int]:
    questions = get_exercise_questions()
    question_ids = [q.id for q in questions]
    random.shuffle(question_ids)
    session[_session_question_order_key()] = question_ids
    session[_session_seen_key()] = []
    session.modified = True
    return question_ids


def get_or_create_question_order() -> List[int]:
    current = session.get(_session_question_order_key())
    if not current:
        return initialize_question_order()
    # keep only ids that still exist and active
    active_ids = {q.id for q in get_exercise_questions()}
    filtered = [qid for qid in current if qid in active_ids]
    if not filtered or len(filtered) != len(current):
        return initialize_question_order()
    return filtered


def mark_question_seen(question_id: int) -> None:
    seen = session.get(_session_seen_key(), [])
    if question_id not in seen:
        seen.append(question_id)
        session[_session_seen_key()] = seen
        session.modified = True


def next_question_index(current_index: int, total_questions: int) -> int:
    return current_index + 1 if current_index + 1 < total_questions else current_index


def parse_options_input(raw_options: str) -> str:
    options = [opt.strip() for opt in raw_options.split("\n") if opt.strip()]
    return json.dumps(options)
