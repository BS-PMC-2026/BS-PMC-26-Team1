import json

from app.models import (
    ExerciseAttempt,
    LearningState,
    Module,
    ModuleProgress,
    ProgressRecord,
    Question,
    TheoryContent,
    db,
)


def _lecturer_question_payload(module_id, **overrides):
    payload = {
        "question_text": "Sprint2 Added Question",
        "question_type": "mcq",
        "correct_answer": "Continuous Integration",
        "explanation": "CI means Continuous Integration.",
        "difficulty": "easy",
        "module_id": str(module_id),
        "options": "Continuous Integration\nContinuous Inspection",
        "starter_code": "",
        "test_cases_json": "",
    }
    payload.update(overrides)
    return payload


def test_learning_path_overview_order_current_and_completion(auth_student_client, student_user):
    auth_student_client.get("/intro")
    response = auth_student_client.get("/learning-path")
    assert response.status_code == 200
    assert b"Learning Path" in response.data
    assert b"Current Step" in response.data
    assert b"Completed" in response.data
    assert b"1/3 modules completed" in response.data

    intro_module = Module.query.filter(Module.name.ilike("intro")).first()
    intro_progress = ModuleProgress.query.filter_by(user_id=student_user.id, module_id=intro_module.id).first()
    assert intro_progress is not None
    assert intro_progress.completed is True


def test_dashboard_shows_module_level_and_overall_progress(auth_student_client):
    auth_student_client.get("/intro")
    auth_student_client.get("/pipeline")
    auth_student_client.post("/exercise?q=0", data={"answer": "Build"})
    response = auth_student_client.get("/progress")
    assert response.status_code == 200
    assert b"Course Progression (Module-Level)" in response.data
    assert b"Exercises Completed Correctly" in response.data
    assert b"Success Rate" in response.data


def test_unified_db_state_tracks_progress_attempts_and_learning_state(auth_student_client, student_user):
    auth_student_client.get("/intro")
    auth_student_client.get("/pipeline")
    auth_student_client.post("/exercise?q=0", data={"answer": "Build"})
    auth_student_client.get("/exercise?q=1")
    auth_student_client.get("/progress")

    record = ProgressRecord.query.filter_by(user_id=student_user.id).first()
    assert record is not None
    assert record.intro_completed is True
    assert record.pipeline_viewed is True
    assert record.total_attempts >= 1

    module_rows = ModuleProgress.query.filter_by(user_id=student_user.id).all()
    assert len(module_rows) >= 3
    assert any(row.completed for row in module_rows)

    attempt = ExerciseAttempt.query.filter_by(user_id=student_user.id).first()
    assert attempt is not None
    assert attempt.question_id is not None

    state = LearningState.query.filter_by(user_id=student_user.id).first()
    assert state is not None
    assert state.last_route in {"/progress", "/exercise", "/learning-path", "/flow/validate"}
    assert state.exercise_question_order_json.startswith("[")


def test_demo_mode_blocks_lecturer_write_routes(client):
    client.get("/demo")
    exercise_module = Module.query.filter(Module.name.ilike("exercise")).first()
    response = client.post(
        "/lecturer/questions/new",
        data=_lecturer_question_payload(exercise_module.id, question_text="Demo Should Not Save"),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/demo-view" in response.headers["Location"]
    assert Question.query.filter_by(question_text="Demo Should Not Save").first() is None


def test_demo_mode_does_not_modify_theory_content(client):
    client.get("/demo")
    intro = Module.query.filter(Module.name.ilike("intro")).first()
    content = TheoryContent.query.filter_by(module_id=intro.id).first()
    original_headline = content.headline
    response = client.post(
        "/lecturer/theory/intro",
        data={
            "headline": "Blocked Update",
            "explanation": "Blocked explanation",
            "examples": "Blocked examples",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/demo-view" in response.headers["Location"]
    db.session.refresh(content)
    assert content.headline == original_headline


def test_lecturer_question_validation_for_module_and_code_json(auth_lecturer_client):
    response_bad_module = auth_lecturer_client.post(
        "/lecturer/questions/new",
        data=_lecturer_question_payload(999999),
        follow_redirects=True,
    )
    assert response_bad_module.status_code == 200
    assert b"required" in response_bad_module.data

    exercise_module = Module.query.filter(Module.name.ilike("exercise")).first()
    response_bad_json = auth_lecturer_client.post(
        "/lecturer/questions/new",
        data=_lecturer_question_payload(
            exercise_module.id,
            question_text="Bad Code JSON",
            question_type="code",
            correct_answer="def solve(a, b):",
            options="",
            starter_code="def solve(a, b):\n    return a+b",
            test_cases_json="{not-json}",
        ),
        follow_redirects=True,
    )
    assert response_bad_json.status_code == 200
    assert b"valid JSON list" in response_bad_json.data


def test_theory_content_update_flow_visible_to_students(app, auth_lecturer_client, student_user):
    response = auth_lecturer_client.post(
        "/lecturer/theory/intro",
        data={
            "headline": "Updated Intro Theory",
            "explanation": "New explanation for CI/CD learning.",
            "examples": "Example: run tests before merge.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/lecturer/theory" in response.headers["Location"]

    student_client = app.test_client()
    student_client.post(
        "/login",
        data={"email": student_user.email, "password": "password123"},
        follow_redirects=False,
    )
    updated_page = student_client.get("/intro")
    assert updated_page.status_code == 200
    assert b"Updated Intro Theory" in updated_page.data
    assert b"run tests before merge" in updated_page.data


def test_pipeline_interaction_contains_click_and_keyboard_states(auth_student_client):
    response = auth_student_client.get("/pipeline")
    assert response.status_code == 200
    assert b"data-stage=" in response.data
    assert b"triggerStage" in response.data
    assert b"active-stage" in response.data


def test_multi_screen_flow_preserves_exercise_order_across_login(client, student_user):
    login = client.post(
        "/login",
        data={"email": student_user.email, "password": "password123"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    client.get("/exercise?random=1")
    state_before = LearningState.query.filter_by(user_id=student_user.id).first()
    assert state_before is not None
    order_before = json.loads(state_before.exercise_question_order_json)
    assert isinstance(order_before, list)
    assert len(order_before) > 0

    client.get("/logout")
    relogin = client.post(
        "/login",
        data={"email": student_user.email, "password": "password123"},
        follow_redirects=False,
    )
    assert relogin.status_code == 302

    with client.session_transaction() as sess:
        assert sess.get("exercise_question_order") == order_before


def test_flow_validate_reports_last_route(auth_student_client):
    auth_student_client.get("/learning-path")
    response = auth_student_client.get("/flow/validate")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["last_route"] in {"/learning-path", "/flow/validate"}
