from app.models import Module, Question, User


def _lecturer_question_payload(module_id, **overrides):
    payload = {
        "question_text": "What does CI stand for?",
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


def test_lecturer_dashboard_access(auth_lecturer_client):
    response = auth_lecturer_client.get("/lecturer/dashboard")
    assert response.status_code == 200
    assert b"Lecturer Dashboard" in response.data


def test_lecturer_question_bank_page_load(auth_lecturer_client):
    response = auth_lecturer_client.get("/lecturer/questions")
    assert response.status_code == 200
    assert b"Question Bank Management" in response.data


def test_lecturer_add_question_success(auth_lecturer_client):
    exercise_module = Module.query.filter(Module.name.ilike("exercise")).first()
    response = auth_lecturer_client.post(
        "/lecturer/questions/new",
        data=_lecturer_question_payload(exercise_module.id),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/lecturer/questions" in response.headers["Location"]

    created = Question.query.filter_by(question_text="What does CI stand for?").first()
    assert created is not None
    assert created.question_type == "mcq"
    assert "Continuous Integration" in created.options_json


def test_lecturer_add_question_validation_failure(auth_lecturer_client):
    exercise_module = Module.query.filter(Module.name.ilike("exercise")).first()
    response = auth_lecturer_client.post(
        "/lecturer/questions/new",
        data=_lecturer_question_payload(exercise_module.id, question_text="", explanation=""),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Question text, answer, explanation, and module are required." in response.data


def test_lecturer_add_code_question_success(auth_lecturer_client):
    exercise_module = Module.query.filter(Module.name.ilike("exercise")).first()
    response = auth_lecturer_client.post(
        "/lecturer/questions/new",
        data=_lecturer_question_payload(
            exercise_module.id,
            question_text="Write solve(a,b)",
            question_type="code",
            correct_answer="def solve(a, b):",
            options="",
            starter_code="def solve(a, b):\n    pass",
            test_cases_json='[{"inputs":[1,2],"expected":3}]',
        ),
        follow_redirects=False,
    )
    assert response.status_code == 302
    created = Question.query.filter_by(question_text="Write solve(a,b)").first()
    assert created is not None
    assert created.options_json == "[]"
    assert created.starter_code is not None
    assert created.test_cases_json is not None


def test_lecturer_edit_question_success(auth_lecturer_client):
    question = Question.query.first()
    module = Module.query.filter(Module.name.ilike("exercise")).first()
    response = auth_lecturer_client.post(
        f"/lecturer/questions/{question.id}/edit",
        data={
            "question_text": "Edited Question",
            "question_type": "open",
            "correct_answer": "devops",
            "explanation": "Edited explanation",
            "difficulty": "hard",
            "module_id": str(module.id),
            "options": "A\nB",
            "starter_code": "ignored",
            "test_cases_json": '[{"inputs":[1,2],"expected":3}]',
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    updated = Question.query.get(question.id)
    assert updated.question_text == "Edited Question"
    assert updated.question_type == "open"
    assert updated.options_json == "[]"
    assert updated.starter_code is None
    assert updated.test_cases_json is None
    assert updated.is_active is False


def test_lecturer_edit_question_code_branch_and_active(auth_lecturer_client):
    question = Question.query.first()
    module = Module.query.filter(Module.name.ilike("exercise")).first()
    response = auth_lecturer_client.post(
        f"/lecturer/questions/{question.id}/edit",
        data={
            "question_text": "Code Question Updated",
            "question_type": "code",
            "correct_answer": "def solve(a, b):",
            "explanation": "Use return",
            "difficulty": "medium",
            "module_id": str(module.id),
            "options": "",
            "starter_code": "def solve(a, b):\n    return a+b",
            "test_cases_json": '[{"inputs":[2,3],"expected":5}]',
            "is_active": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    updated = Question.query.get(question.id)
    assert updated.question_type == "code"
    assert updated.starter_code.startswith("def solve")
    assert updated.test_cases_json.startswith("[")
    assert updated.is_active is True


def test_lecturer_edit_question_invalid_id(auth_lecturer_client):
    response = auth_lecturer_client.get("/lecturer/questions/999999/edit")
    assert response.status_code == 404


def test_lecturer_delete_question_success(auth_lecturer_client):
    question = Question.query.first()
    response = auth_lecturer_client.post(
        f"/lecturer/questions/{question.id}/delete",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert Question.query.get(question.id) is None


def test_lecturer_delete_question_invalid_id(auth_lecturer_client):
    response = auth_lecturer_client.post("/lecturer/questions/999999/delete")
    assert response.status_code == 404


def test_non_lecturer_blocked_from_lecturer_routes(auth_student_client):
    for path in ["/lecturer/dashboard", "/lecturer/questions", "/lecturer/questions/new"]:
        response = auth_student_client.get(path, follow_redirects=False)
        assert response.status_code == 302


def test_unauthenticated_redirected_from_lecturer_routes(client):
    for path in ["/lecturer/dashboard", "/lecturer/questions", "/lecturer/questions/new"]:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")


def test_demo_mode_can_access_lecturer_routes(client):
    client.get("/demo")
    response_dashboard = client.get("/lecturer/dashboard")
    response_questions = client.get("/lecturer/questions")
    assert response_dashboard.status_code == 200
    assert response_questions.status_code == 200
    assert b"Question Bank Management" in response_questions.data


def test_lecturer_question_create_get_renders(auth_lecturer_client):
    response = auth_lecturer_client.get("/lecturer/questions/new")
    assert response.status_code == 200
    assert b"Create Question" in response.data


def test_lecturer_question_edit_get_renders(auth_lecturer_client):
    question = Question.query.first()
    response = auth_lecturer_client.get(f"/lecturer/questions/{question.id}/edit")
    assert response.status_code == 200
    assert b"Edit Question" in response.data


def test_lecturer_dashboard_metrics_include_students(auth_lecturer_client, student_user):
    response = auth_lecturer_client.get("/lecturer/dashboard")
    assert response.status_code == 200
    assert b"Registered Students" in response.data
    assert student_user.full_name.encode() in response.data


def test_lecturer_created_by_is_session_user(auth_lecturer_client, lecturer_user):
    exercise_module = Module.query.filter(Module.name.ilike("exercise")).first()
    auth_lecturer_client.post(
        "/lecturer/questions/new",
        data=_lecturer_question_payload(exercise_module.id, question_text="Session Creator Test"),
        follow_redirects=False,
    )
    created = Question.query.filter_by(question_text="Session Creator Test").first()
    assert created is not None
    assert created.created_by == lecturer_user.id


def test_lecturer_question_bank_handles_no_modules(auth_lecturer_client):
    Module.query.delete()
    from app.models import db

    db.session.commit()
    response = auth_lecturer_client.get("/lecturer/questions")
    assert response.status_code == 200
    assert b"Question Bank Management" in response.data


def test_lecturer_dashboard_with_no_students(auth_lecturer_client):
    User.query.filter_by(role="student").delete()
    from app.models import db

    db.session.commit()
    response = auth_lecturer_client.get("/lecturer/dashboard")
    assert response.status_code == 200
    assert b"Overall Success Average" in response.data
