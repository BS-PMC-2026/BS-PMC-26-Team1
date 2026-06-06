"""BP2T-143: Module Management & System Settings — unit tests."""

from app.models import Module, SystemSetting, db
from app.services.settings_service import (
    DEFAULT_SETTINGS,
    all_settings,
    ensure_defaults,
    get_setting,
    get_setting_int,
    is_maintenance_mode,
    set_setting,
)


# -- positive (modules) ----------------------------------------------------
def test_modules_page_renders(auth_admin_client):
    response = auth_admin_client.get("/admin/modules")
    assert response.status_code == 200
    assert b"Module Management" in response.data


def test_admin_can_create_module(auth_admin_client):
    response = auth_admin_client.post(
        "/admin/modules/new",
        data={
            "name": "Brand New Module",
            "description": "Test description",
            "route": "/brand-new",
            "display_order": "9",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert Module.query.filter_by(name="Brand New Module").first() is not None


def test_admin_can_edit_existing_module(auth_admin_client):
    module = Module(name="EditMe", description="d", route="/editme", display_order=99)
    db.session.add(module)
    db.session.commit()
    auth_admin_client.post(
        f"/admin/modules/{module.id}/edit",
        data={
            "name": "EditMe",
            "description": "updated desc",
            "route": "/editme",
            "display_order": "99",
        },
        follow_redirects=False,
    )
    refreshed = db.session.get(Module, module.id)
    assert refreshed.description == "updated desc"


# -- negative (modules) ----------------------------------------------------
def test_module_create_rejects_duplicate_name(auth_admin_client):
    auth_admin_client.post(
        "/admin/modules/new",
        data={
            "name": "DupMod",
            "description": "first description",
            "route": "/dup",
            "display_order": "1",
        },
    )
    auth_admin_client.post(
        "/admin/modules/new",
        data={
            "name": "DupMod",
            "description": "second description",
            "route": "/dup2",
            "display_order": "2",
        },
        follow_redirects=True,
    )
    # duplicate rejected → only one module with this name
    assert Module.query.filter_by(name="DupMod").count() == 1


def test_module_create_rejects_route_without_slash(auth_admin_client):
    auth_admin_client.post(
        "/admin/modules/new",
        data={
            "name": "BadRoute",
            "description": "desc",
            "route": "noslash",
            "display_order": "1",
        },
        follow_redirects=True,
    )
    assert Module.query.filter_by(name="BadRoute").first() is None


# -- positive (settings) ---------------------------------------------------
def test_default_settings_are_seeded(app):
    ensure_defaults()
    settings = all_settings()
    assert settings["system_name"] == DEFAULT_SETTINGS["system_name"]
    assert settings["maintenance_mode"] == "0"
    assert int(settings["min_password_length"]) >= 6


def test_admin_can_change_setting(auth_admin_client):
    response = auth_admin_client.post(
        "/admin/settings",
        data={
            "system_name": "My Academy",
            "min_password_length": "10",
            "min_completion_score": "75",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert get_setting("system_name") == "My Academy"
    assert get_setting_int("min_password_length", 0) == 10


def test_maintenance_mode_blocks_students(auth_admin_client, auth_student_client):
    set_setting("maintenance_mode", "1")
    db.session.commit()
    response = auth_student_client.get("/intro")
    assert response.status_code == 503
    assert b"under maintenance" in response.data.lower() or b"maintenance" in response.data


# -- edge ------------------------------------------------------------------
def test_maintenance_mode_does_not_block_admin(auth_admin_client):
    set_setting("maintenance_mode", "1")
    db.session.commit()
    response = auth_admin_client.get("/admin/dashboard")
    assert response.status_code == 200
