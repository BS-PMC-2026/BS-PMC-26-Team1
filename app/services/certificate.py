from io import BytesIO

from flask import Blueprint, abort, flash, redirect, render_template, send_file, session, url_for

from app.models import User, db
from app.services.authz import login_required
from app.services.certificate_service import (
    build_certificate_pdf,
    certificate_filename,
    evaluate_certificate,
)

certificate_bp = Blueprint("certificate", __name__)


def _current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


@certificate_bp.route("/certificate")
@login_required
def certificate():
    if session.get("demo_mode"):
        flash("Certificates are not available in demo mode.", "warning")
        return redirect(url_for("main.demo_view"))

    if session.get("role") != "student":
        flash("Certificates are issued to students only.", "warning")
        return redirect(url_for("main.home"))

    user = _current_user()
    if not user:
        flash("Session missing. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    eligibility = evaluate_certificate(user)
    return render_template("certificate.html", eligibility=eligibility)


@certificate_bp.route("/certificate/download")
@login_required
def certificate_download():
    if session.get("demo_mode") or session.get("role") != "student":
        abort(403)
    user = _current_user()
    if not user:
        abort(403)
    eligibility = evaluate_certificate(user)
    if not eligibility.eligible:
        flash("You are not eligible to download the certificate yet.", "error")
        return redirect(url_for("certificate.certificate"))
    pdf_bytes = build_certificate_pdf(eligibility)
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=certificate_filename(user),
    )
