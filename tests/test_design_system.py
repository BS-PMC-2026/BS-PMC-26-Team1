"""
Unit tests for the unified Design System refactor.

Covers the four hackathon-feedback issues from the visual-communication
review plus the follow-up imagery and navigation tweaks:

    Issue 1  – Unified Design System (typography, colors, spacing, buttons)
    Issue 2  – Lecturer Dashboard error handling (ds-alert component)
    Issue 3  – Design System applied across every screen
    Issue 4  – Pipeline information order (Info 1 → 2 → 3 → 4)
    Extra    – Brand imagery (hero illustration + 3 student SVGs)
    Extra    – Standardized stat-number typography
    Extra    – Enlarged navigation typography

All tests render real templates via the Flask test client to make sure
the design tokens actually reach the produced HTML.
"""

from __future__ import annotations

import os
import re

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATIC_DIR = os.path.join(PROJECT_ROOT, "app", "static")
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "app", "templates")
DESIGN_SYSTEM_CSS = os.path.join(STATIC_DIR, "design-system.css")
IMG_DIR = os.path.join(STATIC_DIR, "img")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _all_templates() -> list[str]:
    return sorted(
        os.path.join(TEMPLATES_DIR, name)
        for name in os.listdir(TEMPLATES_DIR)
        if name.endswith(".html")
    )


# ---------------------------------------------------------------------------
# Issue 1 – Unified Design System
# ---------------------------------------------------------------------------

class TestIssue1DesignSystemFile:
    """Verifies the design-system.css file exists and exposes the spec tokens."""

    def test_design_system_file_exists(self):
        assert os.path.isfile(DESIGN_SYSTEM_CSS), "design-system.css must exist"

    def test_main_colors_from_spec(self):
        css = _read(DESIGN_SYSTEM_CSS)
        # Per the spec the main palette must expose these literal hex values
        assert "#FFFFFF" in css        # main text light
        assert "#080D19" in css        # dark navy
        assert "#FEEECA" in css        # cream

    def test_secondary_button_colors(self):
        css = _read(DESIGN_SYSTEM_CSS)
        for hex_value in ("#BCF4DF", "#CEE8FF", "#FFD575", "#F8A21B"):
            assert hex_value in css, f"missing secondary color {hex_value}"

    def test_state_colors(self):
        css = _read(DESIGN_SYSTEM_CSS)
        # In-progress / correct / error per the spec
        assert "#FFE867" in css
        assert "#10B981" in css
        assert "#FF4343" in css

    def test_pill_button_radius(self):
        css = _read(DESIGN_SYSTEM_CSS)
        assert "--ds-radius-btn: 200px" in css, "Buttons must be 200px pills per spec"

    def test_assistant_font_is_declared(self):
        css = _read(DESIGN_SYSTEM_CSS)
        assert "'Assistant'" in css, "Primary font family must be Assistant"

    def test_zero_letter_spacing(self):
        css = _read(DESIGN_SYSTEM_CSS)
        # Spec: all text 0px letter spacing
        assert "letter-spacing: 0" in css

    def test_extra_bold_and_semibold_weights(self):
        css = _read(DESIGN_SYSTEM_CSS)
        # Titles Extra-Bold (800), body Semi-Bold (600)
        assert "--ds-weight-title: 800" in css
        assert "--ds-weight-body: 600" in css

    def test_line_height_follows_size_plus_20px_rule_on_body(self):
        """Per spec: line-height = font-size + 20px. Verified on body size."""
        css = _read(DESIGN_SYSTEM_CSS)
        # --ds-fs-body: 16px → --ds-lh-body should be 36px (16 + 20)
        m_size = re.search(r"--ds-fs-body:\s*(\d+)px", css)
        m_lh = re.search(r"--ds-lh-body:\s*(\d+)px", css)
        assert m_size and m_lh, "body size + line-height tokens must exist"
        assert int(m_lh.group(1)) == int(m_size.group(1)) + 20

    def test_typography_scale_has_responsive_breakpoints(self):
        css = _read(DESIGN_SYSTEM_CSS)
        assert "@media (max-width: 960px)" in css
        assert "@media (max-width: 640px)" in css

    def test_core_components_classes_present(self):
        css = _read(DESIGN_SYSTEM_CSS)
        for klass in (
            ".ds-btn", ".ds-card", ".ds-alert", ".ds-pill",
            ".ds-pipeline", ".ds-pipeline-stage", ".ds-nav",
            ".ds-table", ".ds-stat-number",
        ):
            assert klass in css, f"missing component class {klass}"


class TestIssue1BaseTemplateLoadsDesignSystem:
    """The base.html must load design-system.css and the Assistant font."""

    def test_design_system_loaded_before_legacy_style(self):
        html = _read(os.path.join(TEMPLATES_DIR, "base.html"))
        ds_idx = html.find("filename='design-system.css'")
        legacy_idx = html.find("filename='style.css'")
        assert ds_idx != -1 and legacy_idx != -1, "both stylesheet links must exist"
        assert ds_idx < legacy_idx, "design-system.css must be loaded first"

    def test_assistant_font_link_present(self):
        html = _read(os.path.join(TEMPLATES_DIR, "base.html"))
        assert "Assistant" in html, "Assistant font must be linked in base.html"


# ---------------------------------------------------------------------------
# Issue 2 – Lecturer Dashboard error handling
# ---------------------------------------------------------------------------

class TestIssue2ErrorHandling:
    """The lecturer dashboard must surface lecturer-access errors visibly."""

    def test_alert_component_defined_in_css(self):
        css = _read(DESIGN_SYSTEM_CSS)
        for variant in ("--error", "--success", "--info", "--warning"):
            assert f".ds-alert{variant}" in css, f"alert variant {variant} missing"

    def test_flash_error_renders_through_ds_alert(self, client, student_user):
        """When a student tries to access /lecturer/dashboard the flash
        message must show inside a styled ds-alert--error component."""
        client.post(
            "/login",
            data={"email": student_user.email, "password": "password123"},
            follow_redirects=False,
        )
        response = client.get("/lecturer/dashboard", follow_redirects=True)
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "ds-alert--error" in body, "error must use the design system alert component"
        # The new, more descriptive message must replace the old generic copy.
        assert "Lecturer access is required" in body

    def test_lecturer_dashboard_inline_alert_when_not_lecturer(self, app):
        """Direct rendering of lecturer_dashboard.html with a non-lecturer
        session should still embed the inline ds-alert--error component."""
        from flask import render_template, session

        class _Metrics:
            students_count = 0
            overall_average_success = 0
            student_performance = []
            module_weakness = []

        with app.test_request_context("/lecturer/dashboard"):
            session["role"] = "student"
            session["user_id"] = 999  # any non-lecturer authenticated user
            rendered = render_template(
                "lecturer_dashboard.html", metrics=_Metrics()
            )
        assert "ds-alert--error" in rendered
        assert "Lecturer access required" in rendered

    def test_authz_message_is_descriptive(self):
        """The authz helper carries the new informative copy, not the
        terse 'Student access required.' / 'Lecturer access required.' text."""
        src = _read(os.path.join(PROJECT_ROOT, "app", "services", "authz.py"))
        assert "reserved for student accounts" in src
        assert "Sign in with your lecturer credentials" in src


# ---------------------------------------------------------------------------
# Issue 3 – Design System applied across every screen
# ---------------------------------------------------------------------------

EXPECTED_DS_USERS = [
    "home.html",
    "login.html",
    "register.html",
    "intro.html",
    "pipeline.html",
    "exercise.html",
    "progress.html",
    "learning_path.html",
    "lecturer_dashboard.html",
    "lecturer_questions.html",
    "lecturer_question_form.html",
    "lecturer_theory.html",
    "lecturer_theory_form.html",
    "demo_view.html",
]


class TestIssue3DesignSystemAdoption:

    @pytest.mark.parametrize("template_name", EXPECTED_DS_USERS)
    def test_every_screen_extends_base_and_uses_ds_tokens(self, template_name):
        body = _read(os.path.join(TEMPLATES_DIR, template_name))
        assert "extends 'base.html'" in body, f"{template_name} must extend base.html"
        # At least one design system class or token must be in use
        uses_tokens = any(
            marker in body
            for marker in ("ds-", "var(--ds-", "ds-card", "ds-btn", "ds-alert")
        )
        assert uses_tokens, f"{template_name} should use design system classes"

    def test_no_template_keeps_obsolete_dark_backgrounds(self):
        """The old aurora dark backgrounds (#0b0f19 etc.) should not be
        re-introduced in templates after the refactor."""
        legacy_dark_hex = ("#0b0f19", "#0f172a", "#1e293b")
        offending = []
        for path in _all_templates():
            body = _read(path)
            for hex_value in legacy_dark_hex:
                if hex_value in body:
                    offending.append((os.path.basename(path), hex_value))
        assert not offending, f"Old dark theme hexes still present: {offending}"


# ---------------------------------------------------------------------------
# Issue 4 – Pipeline information order
# ---------------------------------------------------------------------------

EXPECTED_PIPELINE_ORDER = ["code", "build", "test", "deploy"]


class TestIssue4PipelineOrder:

    def test_pipeline_dom_stages_in_canonical_order(self, auth_student_client):
        response = auth_student_client.get("/pipeline")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        # Pull every data-stage="..." that is rendered on an actual element
        stages = re.findall(r'<div[^>]*data-stage="([^"]+)"', body)
        assert stages == EXPECTED_PIPELINE_ORDER, (
            f"pipeline rendered in wrong order: {stages}"
        )

    def test_pipeline_step_numbers_visible_one_to_four(self, auth_student_client):
        response = auth_student_client.get("/pipeline")
        body = response.get_data(as_text=True)
        nums = re.findall(r"ds-pipeline-step-num[^>]*>([0-9]+)<", body)
        assert nums == ["1", "2", "3", "4"]

    def test_pipeline_has_ltr_direction_safeguard(self):
        """The .ds-pipeline rule must lock direction:ltr so the 1→4 order
        is not flipped on a right-to-left page."""
        css = _read(DESIGN_SYSTEM_CSS)
        # Extract the .ds-pipeline rule
        m = re.search(r"\.ds-pipeline\s*\{([^}]+)\}", css)
        assert m, ".ds-pipeline rule must exist"
        assert "direction: ltr" in m.group(1)

    def test_pipeline_template_has_js_order_guardrail(self):
        body = _read(os.path.join(TEMPLATES_DIR, "pipeline.html"))
        assert "PIPELINE_ORDER" in body
        assert "['code', 'build', 'test', 'deploy']" in body


# ---------------------------------------------------------------------------
# Brand imagery + decorative blobs (DEVSKILL-style hero)
# ---------------------------------------------------------------------------

REQUIRED_IMAGES = [
    "hero-learner.svg",
    "student-1.svg",
    "student-2.svg",
    "student-3.svg",
    "learner-cutout.svg",
]


class TestBrandImagery:

    @pytest.mark.parametrize("filename", REQUIRED_IMAGES)
    def test_image_asset_exists_on_disk(self, filename):
        path = os.path.join(IMG_DIR, filename)
        assert os.path.isfile(path), f"missing image asset: {filename}"
        # Sanity: it must be a non-trivial SVG file
        assert os.path.getsize(path) > 256
        assert _read(path).strip().startswith("<svg")

    @pytest.mark.parametrize("filename", REQUIRED_IMAGES)
    def test_image_asset_served_with_200(self, client, filename):
        response = client.get(f"/static/img/{filename}")
        assert response.status_code == 200
        assert b"<svg" in response.data

    def test_home_hero_split_with_imagery(self, client):
        response = client.get("/")
        body = response.get_data(as_text=True)
        assert "ds-hero-split" in body
        assert "ds-hero-image" in body
        assert "hero-learner.svg" in body
        # At least one brand-photography photo-card must appear on the
        # home page (the "12 Weeks" featured path card in the dark
        # mockup), and it must use one of the available student assets.
        assert body.count("ds-photo-card") >= 3, "expected at least one photo-card structure (card + halo + img)"
        assert any(f"student-{i}.svg" in body for i in (1, 2, 3)), \
            "home page should embed at least one brand-photography asset"

    def test_brand_imagery_used_across_app(self, client, auth_student_client):
        """Brand imagery should be exercised across the app, not only on
        the home page. Hero on /, learner cutouts on /intro and
        /learning-path, and a student photo in the home featured path."""
        home = client.get("/").get_data(as_text=True)
        assert "hero-learner.svg" in home
        assert any(f"student-{i}.svg" in home for i in (1, 2, 3))

        intro = auth_student_client.get("/intro").get_data(as_text=True)
        assert "learner-cutout.svg" in intro

        path = auth_student_client.get("/learning-path").get_data(as_text=True)
        assert "learner-cutout.svg" in path

    def test_background_blobs_blend_into_page(self, client):
        """The ds-bg-decor blobs must come from base.html so they show on
        every page (not only the home page)."""
        # Home
        assert "ds-bg-decor" in client.get("/").get_data(as_text=True)
        # Login (anonymous)
        assert "ds-bg-decor" in client.get("/login").get_data(as_text=True)


# ---------------------------------------------------------------------------
# Standardized stat-number typography across dashboards
# ---------------------------------------------------------------------------

class TestStatNumberTypography:

    def test_stat_number_class_defined(self):
        css = _read(DESIGN_SYSTEM_CSS)
        assert ".ds-stat-number" in css
        # Uses the design system stat size token
        m = re.search(r"\.ds-stat-number\s*\{([^}]+)\}", css)
        assert m
        assert "var(--ds-fs-stat)" in m.group(1)

    def test_stat_token_value(self):
        css = _read(DESIGN_SYSTEM_CSS)
        # 48px on desktop, with responsive overrides
        assert "--ds-fs-stat: 48px" in css

    @pytest.mark.parametrize("template_name", ["progress.html", "lecturer_dashboard.html", "demo_view.html"])
    def test_dashboards_use_stat_token_not_inline_size(self, template_name):
        body = _read(os.path.join(TEMPLATES_DIR, template_name))
        assert "ds-stat-number" in body, f"{template_name} should use ds-stat-number"
        # And must not regress to hard-coded numeric font sizes for stats
        assert "font-size:44px" not in body
        assert "font-size: 44px" not in body
        assert "font-size:48px" not in body
        assert "font-size: 48px" not in body


# ---------------------------------------------------------------------------
# Enlarged navigation typography
# ---------------------------------------------------------------------------

class TestNavigationTypography:

    def test_ds_nav_links_use_larger_font_size(self):
        css = _read(DESIGN_SYSTEM_CSS)
        # Pull the .ds-nav-links a rule and verify the bumped size
        m = re.search(r"\.ds-nav-links a\s*\{([^}]+)\}", css)
        assert m
        block = m.group(1)
        assert "font-size: 17px" in block
        assert "var(--ds-weight-title)" in block

    def test_ds_nav_brand_uses_larger_font_size(self):
        css = _read(DESIGN_SYSTEM_CSS)
        m = re.search(r"\.ds-nav-brand\s*\{([^}]+)\}", css)
        assert m
        assert "font-size: 28px" in m.group(1)

    def test_legacy_nav_selectors_match_new_size(self):
        """style.css legacy selectors (.nav-links a) must mirror the
        new size so templates that still reference the old class names
        render identically."""
        css = _read(os.path.join(STATIC_DIR, "style.css"))
        m = re.search(r"\.nav-links a\s*\{([^}]+)\}", css)
        assert m
        assert "font-size: 17px" in m.group(1)


# ---------------------------------------------------------------------------
# Smoke check: every screen renders 200 under the new design system
# ---------------------------------------------------------------------------

class TestEveryScreenStillRenders:

    PUBLIC_PATHS = ["/", "/login", "/register"]
    STUDENT_PATHS = ["/intro", "/pipeline", "/exercise", "/learning-path", "/progress"]
    LECTURER_PATHS = ["/lecturer/dashboard", "/lecturer/questions", "/lecturer/theory"]

    @pytest.mark.parametrize("path", PUBLIC_PATHS)
    def test_public_paths(self, client, path):
        response = client.get(path)
        assert response.status_code == 200
        assert b"design-system.css" in response.data

    @pytest.mark.parametrize("path", STUDENT_PATHS)
    def test_student_paths(self, auth_student_client, path):
        response = auth_student_client.get(path)
        assert response.status_code == 200
        assert b"design-system.css" in response.data

    @pytest.mark.parametrize("path", LECTURER_PATHS)
    def test_lecturer_paths(self, auth_lecturer_client, path):
        response = auth_lecturer_client.get(path)
        assert response.status_code == 200
        assert b"design-system.css" in response.data
