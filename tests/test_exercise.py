import json
from app.models import ExerciseAttempt, ProgressRecord, Question


def test_fetch_questions_from_database(app):
    questions = Question.query.order_by(Question.id.asc()).all()
    assert len(questions) >= 4
    assert all(q.question_text for q in questions)


def test_exercise_route_loads_for_authenticated_user(auth_student_client):
    response = auth_student_client.get("/exercise")
    assert response.status_code == 200
    assert b"CI/CD Concepts" in response.data


def test_navigate_between_questions(auth_student_client):
    response_q1 = auth_student_client.get("/exercise?q=0")
    response_q2 = auth_student_client.get("/exercise?q=1")
    assert response_q1.status_code == 200
    assert response_q2.status_code == 200
    assert b"CI/CD Concepts" in response_q1.data
    assert b"Basic Python Function" in response_q2.data


def test_submit_mcq_correct_answer_and_feedback(auth_student_client, student_user):
    response = auth_student_client.post("/exercise?q=0", data={"answer": "Build"})
    assert response.status_code == 200
    assert b"Correct" in response.data
    assert b"is correct" in response.data

    attempts = ExerciseAttempt.query.filter_by(user_id=student_user.id).all()
    assert len(attempts) == 1
    assert attempts[0].is_correct is True
    assert attempts[0].feedback_text


def test_submit_mcq_incorrect_answer_and_feedback(auth_student_client, student_user):
    response = auth_student_client.post("/exercise?q=0", data={"answer": "Code"})
    assert response.status_code == 200
    assert b"Incorrect" in response.data
    assert b"correct answer is" in response.data

    attempts = ExerciseAttempt.query.filter_by(user_id=student_user.id).all()
    assert len(attempts) == 1
    assert attempts[0].is_correct is False
    assert attempts[0].feedback_text


def test_submit_code_answer_and_receive_feedback(auth_student_client):
    response = auth_student_client.post(
        "/exercise?q=1",
        data={"code_answer": "def solve(a, b):\n    return a + b"},
    )
    assert response.status_code == 200
    assert b"Correct" in response.data
    assert b"All tests passed" in response.data


def test_explanation_exists_for_wrong_code(auth_student_client):
    response = auth_student_client.post(
        "/exercise?q=1",
        data={"code_answer": "def solve(a, b):\n    return a - b"},
    )
    assert response.status_code == 200
    assert b"Incorrect" in response.data
    assert b"Passed" in response.data


def test_run_code_endpoint_requires_authentication(client):
    response = client.post(
        "/exercise/run",
        data=json.dumps({"code": "def solve(a, b):\n    return a + b"}),
        content_type="application/json",
    )
    assert response.status_code == 401


def test_run_code_endpoint_returns_output(auth_student_client):
    response = auth_student_client.post(
        "/exercise/run",
        data=json.dumps({"code": "def solve(a, b):\n    return a + b"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert "output" in payload
    assert "Passed" in payload["output"]


def test_exercise_updates_progress_record(auth_student_client, student_user):
    auth_student_client.post("/exercise?q=0", data={"answer": "Build"})
    record = ProgressRecord.query.filter_by(user_id=student_user.id).first()
    assert record is not None
    assert record.total_attempts == 1
    assert record.correct_answers_count == 1
    assert record.score == 100
