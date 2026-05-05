from app.services.feedback import check_answer


def test_open_ended_question_correct_answer():
    result = check_answer(
        user_answer="I think continuous integration improves quality.",
        expected_answer="continuous integration|ci",
        explanation="Good conceptual match.",
        question_type="open",
    )
    assert result["status"] == "Correct"
    assert result["is_correct"] is True
    assert "Good reflection" in result["explanation"]
    assert result["score"] == 100


def test_open_ended_question_incorrect_answer_long_text_partial_score():
    result = check_answer(
        user_answer="This is a long unrelated answer with many words for scoring logic check.",
        expected_answer="pipeline|deployment",
        explanation="Expected key concept missing.",
        question_type="open",
    )
    assert result["status"] == "Incorrect"
    assert result["is_correct"] is False
    assert "Hint keywords" in result["explanation"]
    assert result["score"] == 40


def test_open_ended_question_incorrect_answer_short_text_zero_score():
    result = check_answer(
        user_answer="wrong words",
        expected_answer="pipeline|deployment",
        explanation="Expected key concept missing.",
        question_type="open",
    )
    assert result["status"] == "Incorrect"
    assert result["is_correct"] is False
    assert result["score"] == 0


def test_empty_explanation_fallback_for_unexpected_type():
    result = check_answer(
        user_answer="some answer",
        expected_answer="some answer",
        explanation="",
        question_type="unexpected-type",
    )
    assert result["status"] == "Incorrect"
    assert result["is_correct"] is False
    assert result["explanation"] == "Please review the material and try again."


def test_malformed_input_handling_none_user_answer():
    result = check_answer(
        user_answer=None,
        expected_answer="Build",
        explanation="",
        question_type="mcq",
    )
    assert result["status"] == "Incorrect"
    assert result["is_correct"] is False
    assert result["explanation"] == "Answer cannot be empty."
    assert result["score"] == 0


def test_malformed_input_handling_none_expected_answer():
    result = check_answer(
        user_answer="Build",
        expected_answer=None,
        explanation="",
        question_type="mcq",
    )
    assert result["status"] == "Incorrect"
    assert result["is_correct"] is False
    assert result["explanation"] == "Answer cannot be empty."


def test_unexpected_question_type_behavior():
    result = check_answer(
        user_answer="any",
        expected_answer="any",
        explanation="custom explanation",
        question_type="essay",
    )
    assert result["status"] == "Incorrect"
    assert result["is_correct"] is False
    assert result["explanation"] == "custom explanation"
    assert result["passed_test_count"] == 0
    assert result["raw_runner_output"] == ""
    assert result["score"] == 0


def test_return_structure_is_exact_and_complete():
    result = check_answer(
        user_answer="Build",
        expected_answer="Build",
        explanation="OK",
        question_type="mcq",
    )
    assert set(result.keys()) == {
        "status",
        "is_correct",
        "explanation",
        "passed_test_count",
        "raw_runner_output",
        "score",
    }


def test_code_question_with_custom_test_cases():
    result = check_answer(
        user_answer="def solve(a, b):\n    return a * b",
        expected_answer="def solve(a, b):",
        explanation="",
        question_type="code",
        test_cases=[{"inputs": [2, 3], "expected": 6}],
    )
    assert result["status"] == "Correct"
    assert result["is_correct"] is True
    assert result["passed_test_count"] == 1
    assert "All tests passed" in result["explanation"]
