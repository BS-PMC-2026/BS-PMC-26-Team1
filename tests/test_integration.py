from app.models import ExerciseAttempt, ProgressRecord, User


def test_full_learning_flow_register_login_intro_pipeline_exercise_dashboard(client):
    register_response = client.post(
        "/register",
        data={
            "username": "integrationstudent",
            "full_name": "Integration Student",
            "email": "integration@student.com",
            "password": "securepass1",
            "confirm_password": "securepass1",
            "role": "student",
        },
        follow_redirects=False,
    )
    assert register_response.status_code == 302
    assert "/login" in register_response.headers["Location"]

    login_response = client.post(
        "/login",
        data={"email": "integration@student.com", "password": "securepass1"},
        follow_redirects=False,
    )
    assert login_response.status_code == 302

    intro_response = client.get("/intro")
    assert intro_response.status_code == 200
    assert b"Introduction to CI/CD" in intro_response.data

    pipeline_response = client.get("/pipeline")
    assert pipeline_response.status_code == 200
    assert b"Visual CI/CD Pipeline" in pipeline_response.data

    exercise_response = client.post("/exercise?q=0", data={"answer": "Build"})
    assert exercise_response.status_code == 200
    assert b"Correct" in exercise_response.data

    dashboard_response = client.get("/progress")
    assert dashboard_response.status_code == 200
    assert b"Your Progress Dashboard" in dashboard_response.data
    assert b"Total Questions Answered" in dashboard_response.data
    assert b"Success Rate" in dashboard_response.data

    user = User.query.filter_by(email="integration@student.com").first()
    assert user is not None

    record = ProgressRecord.query.filter_by(user_id=user.id).first()
    assert record is not None
    assert record.intro_completed is True
    assert record.pipeline_viewed is True
    assert record.total_attempts >= 1
    assert record.correct_answers_count >= 1

    attempts = ExerciseAttempt.query.filter_by(user_id=user.id).all()
    assert len(attempts) >= 1
    assert attempts[0].feedback_text
