from __future__ import annotations

import json
from typing import List, Optional

from flask import session

from app.models import LearningState, Module, db


def _safe_json_list(raw_value: Optional[str]) -> List[int]:
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
        if not isinstance(parsed, list):
            return []
        return [int(item) for item in parsed if isinstance(item, int) or str(item).isdigit()]
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


def get_or_create_learning_state(user_id: int) -> LearningState:
    state = LearningState.query.filter_by(user_id=user_id).first()
    if state:
        return state
    state = LearningState(user_id=user_id)
    db.session.add(state)
    db.session.flush()
    return state


def sync_session_from_learning_state(user_id: int) -> None:
    state = LearningState.query.filter_by(user_id=user_id).first()
    if not state:
        return

    order_ids = _safe_json_list(state.exercise_question_order_json)
    seen_ids = _safe_json_list(state.exercise_seen_ids_json)
    if order_ids:
        session["exercise_question_order"] = order_ids
    if seen_ids:
        session["exercise_seen_ids"] = seen_ids
    if state.last_route:
        session["last_route"] = state.last_route
    session.modified = True


def persist_learning_state(
    user_id: int,
    *,
    current_module_name: Optional[str] = None,
    last_route: Optional[str] = None,
) -> LearningState:
    state = get_or_create_learning_state(user_id)
    if current_module_name:
        module = Module.query.filter(Module.name.ilike(current_module_name)).first()
        if module:
            state.current_module_id = module.id
    if last_route:
        state.last_route = last_route

    state.exercise_question_order_json = json.dumps(session.get("exercise_question_order", []))
    state.exercise_seen_ids_json = json.dumps(session.get("exercise_seen_ids", []))
    return state
