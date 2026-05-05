from app.models import Module, ModuleProgress, ProgressRecord, Question, db


def test_exercise_invalid_question_object_branch_redirects(auth_student_client, monkeypatch):
    monkeypatch.setattr("app.routes.exercise.get_question_by_id", lambda _qid: None)
    response = auth_student_client.get("/exercise", follow_redirects=False)
    assert response.status_code == 302
    assert "/exercise" in response.headers["Location"]


def test_exercise_no_question_order_redirects_home(auth_student_client, monkeypatch):
    monkeypatch.setattr("app.routes.exercise.get_or_create_question_order", lambda: [])
    response = auth_student_client.get("/exercise", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_exercise_out_of_range_q_index_fallback(auth_student_client):
    response = auth_student_client.get("/exercise?q=999")
    assert response.status_code == 200
    assert b"CI/CD Concepts" in response.data


def test_exercise_open_question_submission(auth_student_client, student_user):
    exercise_module = Module.query.filter(Module.name.ilike("exercise")).first()
    open_question = Question(
        question_text="Explain why CI helps quality",
        question_type="open",
        options_json="[]",
        correct_answer="quality|feedback",
        explanation="Focus on fast feedback loops.",
        difficulty="medium",
        module_id=exercise_module.id,
        is_active=True,
    )
    db.session.add(open_question)
    db.session.commit()

    with auth_student_client.session_transaction() as session:
        session["exercise_question_order"] = [open_question.id]
        session["exercise_seen_ids"] = []

    response = auth_student_client.post(
        "/exercise?q=0",
        data={"open_answer": "It improves code quality by fast feedback."},
    )
    assert response.status_code == 200
    assert b"Correct" in response.data or b"Incorrect" in response.data

    record = ProgressRecord.query.filter_by(user_id=student_user.id).first()
    assert record is not None
    assert record.total_attempts >= 1


def test_exercise_missing_answer_submission(auth_student_client):
    response = auth_student_client.post("/exercise?q=0", data={})
    assert response.status_code == 200
    assert b"Answer cannot be empty." in response.data


def test_exercise_malformed_post_data(auth_student_client):
    response = auth_student_client.post("/exercise?q=0", data={"unexpected": "value"})
    assert response.status_code == 200
    assert b"Incorrect" in response.data


def test_exercise_demo_mode_skips_progress_writes(client):
    client.get("/demo")
    with client.session_transaction() as session:
        session["exercise_question_order"] = [1]
        session["exercise_seen_ids"] = []

    response = client.post("/exercise?q=0", data={"answer": "Build"})
    assert response.status_code == 200

    record = ProgressRecord.query.filter_by(user_id=0).first()
    assert record is None


def test_exercise_creates_progress_record_when_missing(auth_student_client, student_user):
    ProgressRecord.query.filter_by(user_id=student_user.id).delete()
    db.session.commit()

    response = auth_student_client.post("/exercise?q=0", data={"answer": "Build"})
    assert response.status_code == 200

    record = ProgressRecord.query.filter_by(user_id=student_user.id).first()
    assert record is not None
    assert record.total_attempts == 1


def test_exercise_random_mode_branch(auth_student_client):
    response = auth_student_client.get("/exercise?random=1&q=0")
    assert response.status_code == 200
    assert b"Shuffle Session" in response.data


def test_exercise_marks_module_completed_when_all_questions_correct(auth_student_client, student_user):
    auth_student_client.post("/exercise?q=0", data={"answer": "Build"})
    auth_student_client.post("/exercise?q=1", data={"code_answer": "def solve(a, b):\n    return a + b"})
    auth_student_client.post("/exercise?q=2", data={"answer": "Automated release without manual approval"})
    auth_student_client.post("/exercise?q=3", data={"answer": "To ensure changes don't break existing features"})

    exercise_module = Module.query.filter(Module.name.ilike("exercise")).first()
    module_row = ModuleProgress.query.filter_by(user_id=student_user.id, module_id=exercise_module.id).first()
    assert module_row is not None
    assert module_row.completed is True
    assert module_row.progress_percentage == 100


def test_exercise_run_code_uses_question_test_cases(auth_student_client):
    code_question = Question.query.filter_by(question_type="code").first()
    response = auth_student_client.post(
        "/exercise/run",
        json={"code": "def solve(a, b):\n    return a + b", "question_id": code_question.id},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert "output" in payload


def test_exercise_run_code_fallback_test_cases_without_question(auth_student_client):
    response = auth_student_client.post(
        "/exercise/run",
        json={"code": "def solve(a, b):\n    return a + b", "question_id": 999999},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert "output" in payload
