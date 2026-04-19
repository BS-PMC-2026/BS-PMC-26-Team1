"""Unit tests for the feedback / check_answer service."""

from app.seed import QuestionType
from app.services.feedback import check_answer


class TestMCQFeedback:

    def test_correct_answer(self):
        result = check_answer(
            user_answer="Build",
            expected_answer="Build",
            question_type=QuestionType.MCQ.value,
        )
        assert result["is_correct"] is True
        assert result["status"] == "Correct"

    def test_incorrect_answer(self):
        result = check_answer(
            user_answer="Deploy",
            expected_answer="Build",
            question_type=QuestionType.MCQ.value,
        )
        assert result["is_correct"] is False
        assert result["status"] == "Incorrect"

    def test_case_insensitive_comparison(self):
        result = check_answer(
            user_answer="build",
            expected_answer="Build",
            question_type=QuestionType.MCQ.value,
        )
        assert result["is_correct"] is True

    def test_whitespace_handling(self):
        result = check_answer(
            user_answer="  Build  ",
            expected_answer="Build",
            question_type=QuestionType.MCQ.value,
        )
        assert result["is_correct"] is True

    def test_has_explanation(self):
        result = check_answer(
            user_answer="Wrong",
            expected_answer="Build",
            explanation="The correct answer is Build.",
            question_type=QuestionType.MCQ.value,
        )
        assert len(result["explanation"]) > 0


class TestEmptyInputFeedback:

    def test_empty_user_answer(self):
        result = check_answer(
            user_answer="",
            expected_answer="Build",
            question_type=QuestionType.MCQ.value,
        )
        assert result["is_correct"] is False
        assert "empty" in result["explanation"].lower()

    def test_none_user_answer(self):
        result = check_answer(
            user_answer=None,
            expected_answer="Build",
            question_type=QuestionType.MCQ.value,
        )
        assert result["is_correct"] is False

    def test_empty_expected_answer(self):
        result = check_answer(
            user_answer="Build",
            expected_answer="",
            question_type=QuestionType.MCQ.value,
        )
        assert result["is_correct"] is False

    def test_none_expected_answer(self):
        result = check_answer(
            user_answer="Build",
            expected_answer=None,
            question_type=QuestionType.MCQ.value,
        )
        assert result["is_correct"] is False


class TestCodeFeedback:
    """Code question feedback — these run actual code through the runner."""

    def test_correct_code(self):
        result = check_answer(
            user_answer="def solve(a, b):\n    return a + b",
            expected_answer="def solve(a, b):",
            question_type=QuestionType.CODE.value,
        )
        assert result["is_correct"] is True
        assert result["passed_test_count"] == 3  # all 3 mock test cases

    def test_incorrect_code(self):
        result = check_answer(
            user_answer="def solve(a, b):\n    return a - b",
            expected_answer="def solve(a, b):",
            question_type=QuestionType.CODE.value,
        )
        assert result["is_correct"] is False
        assert result["passed_test_count"] < 3

    def test_syntax_error_code(self):
        result = check_answer(
            user_answer="def solve(a, b)\n    return a + b",
            expected_answer="def solve(a, b):",
            question_type=QuestionType.CODE.value,
        )
        assert result["is_correct"] is False
        assert result["passed_test_count"] == 0

    def test_partial_pass(self):
        # Only returns correct for inputs (2,3)→5 by hardcoding
        result = check_answer(
            user_answer="def solve(a, b):\n    return 5",
            expected_answer="def solve(a, b):",
            question_type=QuestionType.CODE.value,
        )
        assert result["is_correct"] is False
        assert result["passed_test_count"] >= 1  # at least the (2,3) case


class TestFeedbackReturnStructure:

    def test_return_has_required_keys(self):
        result = check_answer(
            user_answer="Build",
            expected_answer="Build",
            question_type=QuestionType.MCQ.value,
        )
        assert "status" in result
        assert "is_correct" in result
        assert "explanation" in result
        assert "passed_test_count" in result
