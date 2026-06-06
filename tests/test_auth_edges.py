from app.models import User


def test_duplicate_registration_blocked_by_email(client, student_user):
    response = client.post(
        "/register",
        data={
            "username": "anotheruser",
            "full_name": "Dup Email",
            "email": student_user.email,
            "password": "securepass1",
            "confirm_password": "securepass1",
            "role": "student",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Email address already exists." in response.data


def test_duplicate_registration_blocked_by_username(client, student_user):
    response = client.post(
        "/register",
        data={
            "username": student_user.username,
            "full_name": "Dup Username",
            "email": "dup_username@test.com",
            "password": "securepass1",
            "confirm_password": "securepass1",
            "role": "student",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Username already exists." in response.data


def test_invalid_role_handling(client):
    response = client.post(
        "/register",
        data={
            "username": "invalidrole",
            "full_name": "Invalid Role",
            "email": "invalidrole@test.com",
            "password": "securepass1",
            "confirm_password": "securepass1",
            "role": "admin",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Role must be either student or lecturer." in response.data


def test_register_missing_username_and_email_blocked(client):
    response = client.post(
        "/register",
        data={
            "username": "",
            "full_name": "No Username",
            "email": "",
            "password": "securepass1",
            "confirm_password": "securepass1",
            "role": "student",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Username is required." in response.data


def test_demo_login_session_path(client):
    response = client.get("/demo", follow_redirects=False)
    assert response.status_code == 302
    assert "/demo-view" in response.headers["Location"]

    with client.session_transaction() as session:
        assert session["user_id"] == 0
        assert session["role"] == "lecturer"
        assert session["user_name"] == "Demo Lecturer"
        assert session["demo_mode"] is True


def test_login_with_missing_fields(client):
    response = client.post("/login", data={"email": "", "password": ""}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Login failed. Check your email and password." in response.data


def test_logout_when_no_session_exists(client):
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_lecturer_session_values_after_login(client, lecturer_user):
    response = client.post(
        "/login",
        data={"email": lecturer_user.email, "password": "password456"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with client.session_transaction() as session:
        assert session["user_id"] == lecturer_user.id
        assert session["role"] == "lecturer"
        assert session["user_name"] == lecturer_user.full_name
        assert session["demo_mode"] is False


def test_login_get_route_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Welcome Back" in response.data


def test_register_get_route_loads(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create an Account" in response.data


def test_register_success_without_username_uses_email_prefix(client):
    response = client.post(
        "/register",
        data={
            "username": "",
            "full_name": "Auto Username",
            "email": "auto_user@test.com",
            "password": "securepass1",
            "confirm_password": "securepass1",
            "role": "student",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    user = User.query.filter_by(email="auto_user@test.com").first()
    assert user is not None
    assert user.username == "auto_user"
