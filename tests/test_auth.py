from app.models import LecturerProfile, StudentProfile, User


def test_register_user_student(client):
    response = client.post(
        "/register",
        data={
            "username": "newstudent",
            "full_name": "New Student",
            "email": "newstudent@test.com",
            "password": "securepass1",
            "confirm_password": "securepass1",
            "role": "student",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    user = User.query.filter_by(email="newstudent@test.com").first()
    assert user is not None
    assert user.username == "newstudent"
    assert user.role == "student"
    assert StudentProfile.query.filter_by(user_id=user.id).first() is not None


def test_register_user_lecturer(client):
    response = client.post(
        "/register",
        data={
            "username": "newlecturer",
            "full_name": "New Lecturer",
            "email": "newlecturer@test.com",
            "password": "securepass1",
            "confirm_password": "securepass1",
            "role": "lecturer",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    user = User.query.filter_by(email="newlecturer@test.com").first()
    assert user is not None
    assert user.role == "lecturer"
    assert LecturerProfile.query.filter_by(user_id=user.id).first() is not None


def test_login_user_success(client, student_user):
    response = client.post(
        "/login",
        data={"email": student_user.email, "password": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session["user_id"] == student_user.id
        assert session["role"] == "student"
        assert session["user_name"] == student_user.full_name


def test_invalid_login_rejected(client, student_user):
    response = client.post(
        "/login",
        data={"email": student_user.email, "password": "wrong-password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Login failed" in response.data
    with client.session_transaction() as session:
        assert session.get("user_id") is None


def test_session_persistence_between_requests(auth_student_client, student_user):
    response = auth_student_client.get("/learning-path")
    assert response.status_code == 200
    with auth_student_client.session_transaction() as session:
        assert session["user_id"] == student_user.id
        assert session["role"] == "student"


def test_logout_clears_session(auth_student_client):
    response = auth_student_client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with auth_student_client.session_transaction() as session:
        assert session.get("user_id") is None
        assert session.get("role") is None
        assert session.get("user_name") is None
