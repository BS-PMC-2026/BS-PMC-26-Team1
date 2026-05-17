from functools import wraps

from flask import flash, redirect, session, url_for


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id") and not session.get("demo_mode"):
            flash("Please login to continue.", "error")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped


def student_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id") and not session.get("demo_mode"):
            flash("Please log in to continue your learning path.", "error")
            return redirect(url_for("auth.login"))
        if session.get("demo_mode"):
            return view_func(*args, **kwargs)
        if session.get("role") != "student":
            flash(
                "This page is reserved for student accounts. "
                "Use the Lecturer Dashboard to manage questions and theory content.",
                "error",
            )
            return redirect(url_for("main.home"))
        return view_func(*args, **kwargs)

    return wrapped


def lecturer_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if session.get("demo_mode"):
            return view_func(*args, **kwargs)
        if not session.get("user_id") or session.get("role") != "lecturer":
            flash(
                "Lecturer access is required for this screen. "
                "Sign in with your lecturer credentials to view analytics and manage content.",
                "error",
            )
            return redirect(url_for("main.home"))
        return view_func(*args, **kwargs)

    return wrapped
