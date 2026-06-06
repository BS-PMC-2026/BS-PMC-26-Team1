from flask import session

from app.models import LearningState, Module, db
from app.services.state_service import persist_learning_state, sync_session_from_learning_state


def test_persist_learning_state_creates_record(app, student_user):
    with app.test_request_context("/exercise"):
        session["exercise_question_order"] = [1, 2, 3]
        session["exercise_seen_ids"] = [1]
        state = persist_learning_state(
            student_user.id,
            current_module_name="Exercise",
            last_route="/exercise",
        )
        db.session.commit()
        assert state.user_id == student_user.id
        assert state.last_route == "/exercise"
        assert state.exercise_question_order_json == "[1, 2, 3]"
        assert state.exercise_seen_ids_json == "[1]"


def test_sync_session_from_learning_state_restores_values(app, student_user):
    exercise = Module.query.filter(Module.name.ilike("exercise")).first()
    state = LearningState(
        user_id=student_user.id,
        current_module_id=exercise.id,
        last_route="/progress",
        exercise_question_order_json="[4, 3, 2]",
        exercise_seen_ids_json="[4, 3]",
    )
    db.session.add(state)
    db.session.commit()

    with app.test_request_context("/login"):
        sync_session_from_learning_state(student_user.id)
        assert session.get("exercise_question_order") == [4, 3, 2]
        assert session.get("exercise_seen_ids") == [4, 3]
        assert session.get("last_route") == "/progress"
