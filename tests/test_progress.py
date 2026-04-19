from app.models import ExerciseAttempt, Module, ModuleProgress, ProgressRecord, Question, User, db


def test_progress_route_requires_authentication(client):
    response = client.get("/progress", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_progress_dashboard_loads(auth_student_client, student_user):
    response = auth_student_client.get("/progress")
    assert response.status_code == 200
    assert b"Your Progress Dashboard" in response.data
    assert student_user.full_name.encode() in response.data


def test_progress_updates_after_intro(auth_student_client, student_user):
    auth_student_client.get("/intro")
    record = ProgressRecord.query.filter_by(user_id=student_user.id).first()
    assert record is not None
    assert record.intro_completed is True


def test_progress_updates_after_pipeline(auth_student_client, student_user):
    auth_student_client.get("/pipeline")
    record = ProgressRecord.query.filter_by(user_id=student_user.id).first()
    assert record is not None
    assert record.pipeline_viewed is True


def test_progress_updates_after_exercise(auth_student_client, student_user):
    auth_student_client.post("/exercise?q=0", data={"answer": "Build"})
    record = ProgressRecord.query.filter_by(user_id=student_user.id).first()
    assert record is not None
    assert record.total_attempts == 1
    assert record.correct_answers_count == 1


def test_dashboard_shows_calculated_success_rate(auth_student_client, student_user):
    auth_student_client.post("/exercise?q=0", data={"answer": "Build"})
    auth_student_client.post("/exercise?q=0", data={"answer": "Wrong"})
    record = ProgressRecord.query.filter_by(user_id=student_user.id).first()
    assert record.score == 50

    response = auth_student_client.get("/progress")
    assert response.status_code == 200
    assert b"50%" in response.data
    assert b"Success Rate" in response.data


def test_dashboard_shows_attempt_activity(auth_student_client):
    auth_student_client.post("/exercise?q=0", data={"answer": "Build"})
    response = auth_student_client.get("/progress")
    assert response.status_code == 200
    assert b"Recent Activity Log" in response.data
    assert b"Correct" in response.data


def test_model_user_insert_update_query(db_session):
    user = User(
        username="modeluser",
        full_name="Model User",
        email="model@test.com",
        password_hash="hash",
        role="student",
    )
    db_session.add(user)
    db_session.commit()

    fetched = User.query.filter_by(email="model@test.com").first()
    assert fetched is not None
    fetched.full_name = "Updated User"
    db_session.commit()
    fetched_again = User.query.filter_by(email="model@test.com").first()
    assert fetched_again.full_name == "Updated User"


def test_model_question_insert_update_query(db_session):
    exercise_module = Module.query.filter(Module.name.ilike("exercise")).first()
    question = Question(
        question_text="What is CI?",
        question_type="mcq",
        options_json='["A","B"]',
        correct_answer="A",
        explanation="Explanation",
        difficulty="easy",
        module_id=exercise_module.id,
        is_active=True,
    )
    db_session.add(question)
    db_session.commit()

    fetched = Question.query.filter_by(question_text="What is CI?").first()
    assert fetched is not None
    fetched.correct_answer = "B"
    db_session.commit()
    assert Question.query.get(fetched.id).correct_answer == "B"


def test_model_exercise_attempt_insert_update_query(db_session, student_user):
    attempt = ExerciseAttempt(
        user_id=student_user.id,
        question_id=1,
        answer="Build",
        is_correct=True,
        feedback_text="Good",
        score=100,
    )
    db_session.add(attempt)
    db_session.commit()

    fetched = ExerciseAttempt.query.filter_by(user_id=student_user.id).first()
    assert fetched is not None
    fetched.is_correct = False
    db_session.commit()
    assert ExerciseAttempt.query.get(fetched.id).is_correct is False


def test_model_progress_record_insert_update_query(db_session, student_user):
    record = ProgressRecord(user_id=student_user.id, intro_completed=False)
    db_session.add(record)
    db_session.commit()

    fetched = ProgressRecord.query.filter_by(user_id=student_user.id).first()
    assert fetched is not None
    fetched.intro_completed = True
    db_session.commit()
    assert ProgressRecord.query.get(fetched.id).intro_completed is True


def test_model_module_progress_insert_update_query(db_session, student_user):
    intro_module = Module.query.filter(Module.name.ilike("intro")).first()
    row = ModuleProgress(
        user_id=student_user.id,
        module_id=intro_module.id,
        completed=False,
        progress_percentage=25,
    )
    db_session.add(row)
    db_session.commit()

    fetched = ModuleProgress.query.filter_by(user_id=student_user.id, module_id=intro_module.id).first()
    assert fetched is not None
    fetched.progress_percentage = 100
    fetched.completed = True
    db_session.commit()

    verified = ModuleProgress.query.filter_by(user_id=student_user.id, module_id=intro_module.id).first()
    assert verified.progress_percentage == 100
    assert verified.completed is True
