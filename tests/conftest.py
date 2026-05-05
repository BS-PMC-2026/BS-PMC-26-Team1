import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.models import LecturerProfile, StudentProfile, User, db as _db


@pytest.fixture(scope="function")
def app():
    application = create_app(
        test_config={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "SECRET_KEY": "test-secret-key",
        }
    )
    with application.app_context():
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    return _db.session


@pytest.fixture(scope="function")
def student_user(app):
    user = User(
        username="student",
        full_name="Test Student",
        email="student@test.com",
        password_hash=generate_password_hash("password123"),
        role="student",
    )
    _db.session.add(user)
    _db.session.flush()
    _db.session.add(StudentProfile(user_id=user.id))
    _db.session.commit()
    return user


@pytest.fixture(scope="function")
def lecturer_user(app):
    user = User(
        username="lecturer",
        full_name="Test Lecturer",
        email="lecturer@test.com",
        password_hash=generate_password_hash("password456"),
        role="lecturer",
    )
    _db.session.add(user)
    _db.session.flush()
    _db.session.add(LecturerProfile(user_id=user.id))
    _db.session.commit()
    return user


@pytest.fixture(scope="function")
def auth_student_client(client, student_user):
    response = client.post(
        "/login",
        data={"email": student_user.email, "password": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    return client


@pytest.fixture(scope="function")
def auth_lecturer_client(client, lecturer_user):
    response = client.post(
        "/login",
        data={"email": lecturer_user.email, "password": "password456"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    return client


@pytest.fixture(scope="function")
def sample_student(student_user):
    return {
        "id": student_user.id,
        "full_name": student_user.full_name,
        "email": student_user.email,
        "password": "password123",
        "role": student_user.role,
    }


@pytest.fixture(scope="function")
def sample_lecturer(lecturer_user):
    return {
        "id": lecturer_user.id,
        "full_name": lecturer_user.full_name,
        "email": lecturer_user.email,
        "password": "password456",
        "role": lecturer_user.role,
    }


@pytest.fixture(scope="function")
def auth_client(auth_student_client):
    return auth_student_client
