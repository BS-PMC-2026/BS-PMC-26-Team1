"""Tests for the homepage and /start route."""


class TestHomepage:

    def test_homepage_returns_200(self, client):
        rv = client.get("/")
        assert rv.status_code == 200

    def test_homepage_has_start_learning_button(self, client):
        rv = client.get("/")
        assert b"Start Learning" in rv.data

    def test_homepage_has_platform_title(self, client):
        rv = client.get("/")
        assert b"CI/CD Learning Platform" in rv.data

    def test_homepage_contains_start_link(self, client):
        rv = client.get("/")
        assert b"/start" in rv.data


class TestStartRoute:

    def test_redirects_to_login_when_unauthenticated(self, client):
        rv = client.get("/start", follow_redirects=False)
        assert rv.status_code == 302
        assert "/login" in rv.headers.get("Location", "")

    def test_redirects_to_intro_when_authenticated(self, auth_client):
        rv = auth_client.get("/start", follow_redirects=False)
        assert rv.status_code == 302
        assert "/intro" in rv.headers.get("Location", "")
