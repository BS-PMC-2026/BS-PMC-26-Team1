import json

from app.models import Module, Question, db
from app.services.code_runner_service import run_student_code
from app.services.question_service import serialize_question
from app.seed import QuestionType


def test_code_question_metadata_in_serialize(auth_student_client):
    code_question = Question.query.filter_by(question_type=QuestionType.CODE.value).first()
    assert code_question is not None
    data = serialize_question(code_question)
    assert data["type"] == "code"
    assert data["language"] == "python"
    assert data["display_language"] == "Python"
    assert data["compiler_info"]
    assert data["execution_environment"]
    assert "sandbox" in data["execution_environment"].lower() or "secure" in data[
        "execution_environment"
    ].lower()


def test_exercise_page_displays_environment_block(auth_student_client):
    response = auth_student_client.get("/exercise?q=1")
    assert response.status_code == 200
    assert b"Language:" in response.data
    assert b"Interpreter:" in response.data
    assert b"Environment:" in response.data


def test_run_student_code_execution_result_correct(auth_student_client):
    response = auth_student_client.post(
        "/exercise/run",
        data=json.dumps(
            {"code": "def solve(a, b):\n    return a + b", "question_id": None}
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert "output" in payload
    assert "Passed" in payload["output"]


def test_run_student_code_unsupported_language_safe_message():
    out = run_student_code(
        "def solve(a,b): return 0",
        [{"inputs": [1, 2], "expected": 3}],
        language="rust",
    )
    assert out["passed"] == 0
    assert "Unsupported language" in out["output_log"]


def test_run_student_code_restricted_import_blocked():
    out = run_student_code(
        "import os\ndef solve(a, b):\n    return a + b",
        [{"inputs": [2, 3], "expected": 5}],
        language="python",
    )
    assert out["passed"] == 0
    assert "Restricted import" in out["output_log"]


def test_run_student_code_malformed_does_not_raise():
    out = run_student_code(
        "this is not valid python {{{",
        [{"inputs": [1, 2], "expected": 3}],
        language="python",
    )
    assert "passed" in out
    assert out["passed"] == 0
    assert "Syntax" in out["output_log"] or "Error" in out["output_log"]


def test_serialize_defaults_when_code_metadata_null(app):
    exercise_module = Module.query.filter(Module.name.ilike("Exercise")).first()
    q = Question(
        question_text="Temp code",
        question_type=QuestionType.CODE.value,
        options_json="[]",
        correct_answer="x",
        explanation="e",
        difficulty="easy",
        module_id=exercise_module.id,
        starter_code="def solve(a,b):\n    pass",
        test_cases_json=json.dumps([{"inputs": [1, 2], "expected": 3}]),
        language=None,
        execution_environment=None,
        compiler_info=None,
        is_active=True,
    )
    db.session.add(q)
    db.session.commit()
    try:
        data = serialize_question(q)
        assert data["language"] == "python"
        assert data["compiler_info"]
        assert data["execution_environment"]
    finally:
        db.session.delete(q)
        db.session.commit()
