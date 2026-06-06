"""BP2T-121: Admin Role Foundation — unit tests."""

from werkzeug.security import check_password_hash, generate_password_hash

from app.models import AdminProfile, User, db
from app.services.authz import admin_required


# -- positive --------------------------------------------------------------
def test_default_admin_user_is_seeded(app):
    admin = User.query.filter_by(email="admin@ante.local").first()
    assert admin is not None
    assert admin.role == "admin"
    assert admin.is_active is True


def test_admin_profile_row_exists_for_seeded_admin(app):
    admin = User.query.filter_by(role="admin").first()
    profile = AdminProfile.query.filter_by(user_id=admin.id).first()
    assert profile is not None
    assert profile.admin_id  # non-empty


def test_admin_required_allows_admin_session(auth_admin_client):
    response = auth_admin_client.get("/admin/dashboard")
    assert response.status_code == 200


# -- negative --------------------------------------------------------------
def test_admin_required_blocks_student(auth_student_client):
    response = auth_student_client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_required_blocks_lecturer(auth_lecturer_client):
    response = auth_lecturer_client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 302


def test_admin_required_blocks_anonymous(client):
    response = client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 302


# -- edge ------------------------------------------------------------------
def test_register_blocks_admin_role(client):
    response = client.post(
        "/register",
        data={
            "username": "wannabeadmin",
            "full_name": "Wannabe Admin",
            "email": "wannabe@x.com",
            "password": "secret123",
            "confirm_password": "secret123",
            "role": "admin",
        },
        follow_redirects=False,
    )
    # form rejects admin role and redirects back to register
    assert response.status_code == 302
    assert "/register" in response.headers["Location"]
    assert User.query.filter_by(email="wannabe@x.com").first() is None
