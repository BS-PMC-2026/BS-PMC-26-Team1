from sqlalchemy import text

from app.models import db


def _table_exists(table_name: str) -> bool:
    rows = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name},
    ).fetchall()
    return bool(rows)


def _table_columns(table_name: str) -> set[str]:
    rows = db.session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def ensure_schema_compatibility() -> None:
    """
    Lightweight SQLite evolution helper for local environments without Alembic.
    Adds missing columns used by the upgraded academic system.
    """
    if db.engine.dialect.name != "sqlite":
        return

    if _table_exists("users"):
        columns = _table_columns("users")
        if "username" not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(80)"))

    if _table_exists("questions"):
        columns = _table_columns("questions")
        if "question_text" not in columns:
            db.session.execute(text("ALTER TABLE questions ADD COLUMN question_text TEXT"))
        if "options_json" not in columns:
            db.session.execute(text("ALTER TABLE questions ADD COLUMN options_json TEXT"))
        if "correct_answer" not in columns:
            db.session.execute(text("ALTER TABLE questions ADD COLUMN correct_answer TEXT"))
        if "module_id" not in columns:
            db.session.execute(text("ALTER TABLE questions ADD COLUMN module_id INTEGER"))
        if "test_cases_json" not in columns:
            db.session.execute(text("ALTER TABLE questions ADD COLUMN test_cases_json TEXT"))
        if "created_at" not in columns:
            db.session.execute(text("ALTER TABLE questions ADD COLUMN created_at DATETIME"))
        if "updated_at" not in columns:
            db.session.execute(text("ALTER TABLE questions ADD COLUMN updated_at DATETIME"))

    if _table_exists("exercise_attempts"):
        columns = _table_columns("exercise_attempts")
        if "answer" not in columns:
            db.session.execute(text("ALTER TABLE exercise_attempts ADD COLUMN answer TEXT"))

    db.session.commit()
