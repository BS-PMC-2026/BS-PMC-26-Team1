from sqlalchemy import text

from app.models import Module, Question, db
from app.seed import bootstrap_database
from app.services.db_init import ensure_schema_compatibility


def _columns_for(table_name):
    rows = db.session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def test_database_initialization_runs_without_error(app):
    ensure_schema_compatibility()
    assert Module.query.count() >= 1


def test_module_seed_creation_when_empty(app):
    Question.query.delete()
    Module.query.delete()
    db.session.commit()

    bootstrap_database()

    modules = Module.query.order_by(Module.display_order.asc()).all()
    assert len(modules) >= 3
    names = {m.name.lower() for m in modules}
    assert {"intro", "pipeline", "exercise"}.issubset(names)


def test_question_seed_creation_when_empty(app):
    Question.query.delete()
    db.session.commit()

    bootstrap_database()
    assert Question.query.count() >= 4


def test_no_duplicate_seeding_on_repeated_calls(app):
    bootstrap_database()
    first_module_count = Module.query.count()
    first_question_count = Question.query.count()

    bootstrap_database()
    second_module_count = Module.query.count()
    second_question_count = Question.query.count()

    assert second_module_count == first_module_count
    assert second_question_count == first_question_count


def test_empty_database_bootstrap_logic(app):
    Question.query.delete()
    Module.query.delete()
    db.session.commit()

    assert Module.query.count() == 0
    assert Question.query.count() == 0

    bootstrap_database()

    assert Module.query.count() > 0
    assert Question.query.count() > 0


def test_schema_compatibility_adds_missing_users_username(app):
    db.session.execute(text("DROP TABLE IF EXISTS users"))
    db.session.execute(
        text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, full_name VARCHAR(100), email VARCHAR(120), password_hash VARCHAR(255), role VARCHAR(20))"
        )
    )
    db.session.commit()

    ensure_schema_compatibility()
    columns = _columns_for("users")
    assert "username" in columns


def test_schema_compatibility_adds_missing_questions_columns(app):
    db.session.execute(text("DROP TABLE IF EXISTS questions"))
    db.session.execute(
        text(
            "CREATE TABLE questions (id INTEGER PRIMARY KEY, question_type VARCHAR(20), explanation TEXT, difficulty VARCHAR(50), is_active BOOLEAN)"
        )
    )
    db.session.commit()

    ensure_schema_compatibility()
    columns = _columns_for("questions")
    expected = {
        "question_text",
        "options_json",
        "correct_answer",
        "module_id",
        "test_cases_json",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns)


def test_schema_compatibility_adds_missing_exercise_attempt_answer(app):
    db.session.execute(text("DROP TABLE IF EXISTS exercise_attempts"))
    db.session.execute(
        text(
            "CREATE TABLE exercise_attempts (id INTEGER PRIMARY KEY, user_id INTEGER, question_id INTEGER, is_correct BOOLEAN)"
        )
    )
    db.session.commit()

    ensure_schema_compatibility()
    columns = _columns_for("exercise_attempts")
    assert "answer" in columns


def test_schema_compatibility_safe_when_tables_missing(app):
    db.session.execute(text("DROP TABLE IF EXISTS users"))
    db.session.execute(text("DROP TABLE IF EXISTS questions"))
    db.session.execute(text("DROP TABLE IF EXISTS exercise_attempts"))
    db.session.commit()

    ensure_schema_compatibility()

    users_exists = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    ).fetchall()
    assert users_exists == []
