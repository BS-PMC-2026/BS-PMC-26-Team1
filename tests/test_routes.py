def test_home_route_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to CI/CD Learning Platform" in response.data


def test_learning_path_requires_auth(client):
    response = client.get("/learning-path", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_learning_path_loads_for_student(auth_student_client):
    response = auth_student_client.get("/learning-path")
    assert response.status_code == 200
    assert b"Learning Path" in response.data


def test_intro_route_requires_auth(client):
    response = client.get("/intro", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_intro_route_loads(auth_student_client):
    response = auth_student_client.get("/intro")
    assert response.status_code == 200
    assert b"Introduction to CI/CD" in response.data


def test_pipeline_route_requires_auth(client):
    response = client.get("/pipeline", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_pipeline_route_loads(auth_student_client):
    response = auth_student_client.get("/pipeline")
    assert response.status_code == 200
    assert b"Visual CI/CD Pipeline" in response.data


def test_pipeline_stage_explanations_exist(auth_student_client):
    response = auth_student_client.get("/pipeline")
    assert response.status_code == 200
    assert b"Code & Commit" in response.data
    assert b"Build Process" in response.data
    assert b"Automated Testing" in response.data
    assert b"Deployment" in response.data


def test_exercise_route_requires_auth(client):
    response = client.get("/exercise", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_exercise_route_loads(auth_student_client):
    response = auth_student_client.get("/exercise")
    assert response.status_code == 200
    assert b"CI/CD Concepts" in response.data


def test_progress_route_requires_auth(client):
    response = client.get("/progress", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_progress_route_loads(auth_student_client):
    response = auth_student_client.get("/progress")
    assert response.status_code == 200
    assert b"Your Progress Dashboard" in response.data


def test_demo_route_sets_demo_mode(client):
    response = client.get("/demo", follow_redirects=False)
    assert response.status_code == 302
    assert "/demo-view" in response.headers["Location"]
    with client.session_transaction() as session:
        assert session["demo_mode"] is True
        assert session["role"] == "lecturer"


def test_demo_view_loads_after_demo_toggle(client):
    client.get("/demo")
    response = client.get("/demo-view")
    assert response.status_code == 200
    assert b"Lecturer Demo View" in response.data


def test_student_cannot_access_lecturer_dashboard(auth_student_client):
    response = auth_student_client.get("/lecturer/dashboard", follow_redirects=False)
    assert response.status_code == 302


def test_student_cannot_access_lecturer_management(auth_student_client):
    response = auth_student_client.get("/lecturer/questions", follow_redirects=False)
    assert response.status_code == 302


def test_lecturer_can_access_dashboard(auth_lecturer_client):
    response = auth_lecturer_client.get("/lecturer/dashboard")
    assert response.status_code == 200
    assert b"Lecturer Dashboard" in response.data


def test_lecturer_can_access_question_bank(auth_lecturer_client):
    response = auth_lecturer_client.get("/lecturer/questions")
    assert response.status_code == 200
    assert b"Question Bank Management" in response.data
