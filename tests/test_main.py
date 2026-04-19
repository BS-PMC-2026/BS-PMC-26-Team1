from app.models import Module, ModuleProgress, ProgressRecord, db


def test_home_route_guest_state(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"New student? Create account" in response.data


def test_home_route_authenticated_state(auth_student_client):
    response = auth_student_client.get("/")
    assert response.status_code == 200
    assert b"Continue from Learning Path" in response.data


def test_home_route_demo_state(client):
    client.get("/demo")
    response = client.get("/")
    assert response.status_code == 200
    assert b"Continue from Learning Path" in response.data


def test_start_route_redirects_to_login_for_guest(client):
    response = client.get("/start", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_start_route_redirects_student_to_intro(auth_student_client):
    response = auth_student_client.get("/start", follow_redirects=False)
    assert response.status_code == 302
    assert "/intro" in response.headers["Location"]


def test_start_route_redirects_lecturer_to_dashboard(auth_lecturer_client):
    response = auth_lecturer_client.get("/start", follow_redirects=False)
    assert response.status_code == 302
    assert "/lecturer/dashboard" in response.headers["Location"]


def test_start_route_redirects_demo_to_demo_view(client):
    client.get("/demo")
    response = client.get("/start", follow_redirects=False)
    assert response.status_code == 302
    assert "/demo-view" in response.headers["Location"]


def test_learning_path_redirect_for_unauthenticated(client):
    response = client.get("/learning-path", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_learning_path_for_authenticated_student(auth_student_client):
    response = auth_student_client.get("/learning-path")
    assert response.status_code == 200
    assert b"Learning Path" in response.data
    assert b"Overall module completion" in response.data


def test_learning_path_redirect_for_lecturer(auth_lecturer_client):
    response = auth_lecturer_client.get("/learning-path", follow_redirects=False)
    assert response.status_code == 302
    assert "/lecturer/dashboard" in response.headers["Location"]


def test_learning_path_demo_branch(client):
    client.get("/demo")
    response = client.get("/learning-path")
    assert response.status_code == 200
    assert b"Lecturer Demo Mode" in response.data


def test_demo_view_redirect_when_not_demo(client):
    response = client.get("/demo-view", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_demo_view_route(client):
    client.get("/demo")
    response = client.get("/demo-view")
    assert response.status_code == 200
    assert b"Lecturer Demo View" in response.data
    assert b"Demo Flow" in response.data


def test_flow_validate_redirect_when_not_authenticated(client):
    response = client.get("/flow/validate", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_flow_validate_returns_json_for_authenticated_user(auth_student_client, student_user):
    response = auth_student_client.get("/flow/validate")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["user_id"] == student_user.id
    assert "next_route" in payload
    assert "modules_total" in payload
    assert "modules_completed" in payload
    assert "module_percent" in payload


def test_flow_validate_next_route_progress_when_all_completed(auth_student_client, student_user):
    modules = Module.query.order_by(Module.display_order.asc()).all()
    module_rows = ModuleProgress.query.filter_by(user_id=student_user.id).all()
    by_module = {row.module_id: row for row in module_rows}
    for module in modules:
        row = by_module.get(module.id)
        if row is None:
            row = ModuleProgress(
                user_id=student_user.id,
                module_id=module.id,
                completed=True,
                progress_percentage=100,
            )
            db.session.add(row)
        else:
            row.completed = True
            row.progress_percentage = 100
    db.session.commit()

    record = ProgressRecord.query.filter_by(user_id=student_user.id).first()
    if record is None:
        record = ProgressRecord(user_id=student_user.id)
        db.session.add(record)
    record.intro_completed = True
    record.pipeline_viewed = True
    record.exercise_completed = True
    db.session.commit()

    response = auth_student_client.get("/flow/validate")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["next_route"] == "/progress"


def test_flow_validate_returns_first_incomplete_route(auth_student_client):
    response = auth_student_client.get("/flow/validate")
    payload = response.get_json()
    assert payload["next_route"] in {"/intro", "/pipeline", "/exercise", "/progress"}
