"""Unit tests for the code runner sandbox service."""

from app.services.code_runner_service import run_student_code


# Standard test cases used across tests (matching what the app uses)
BASIC_TEST_CASES = [
    {"inputs": [2, 3], "expected": 5},
    {"inputs": [-1, 1], "expected": 0},
]


class TestCorrectCode:

    def test_all_tests_pass(self):
        code = "def solve(a, b):\n    return a + b"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert result["passed"] == 2
        assert result["total"] == 2
        assert "Passed" in result["output_log"]

    def test_output_log_per_case(self):
        code = "def solve(a, b):\n    return a + b"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert "Test 1 Passed" in result["output_log"]
        assert "Test 2 Passed" in result["output_log"]


class TestIncorrectCode:

    def test_wrong_logic_fails(self):
        code = "def solve(a, b):\n    return a - b"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert result["passed"] < 2
        assert "Failed" in result["output_log"]

    def test_hardcoded_value_partial(self):
        code = "def solve(a, b):\n    return 5"
        result = run_student_code(code, BASIC_TEST_CASES)

        # (2,3) → 5 passes, (-1,1) → 5 fails
        assert result["passed"] == 1


class TestSyntaxErrors:

    def test_syntax_error_caught(self):
        code = "def solve(a, b)\n    return a + b"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert result["passed"] == 0
        assert "Error" in result["output_log"]

    def test_indentation_error(self):
        code = "def solve(a, b):\nreturn a + b"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert result["passed"] == 0
        assert "Error" in result["output_log"]


class TestMissingSolveFunction:

    def test_missing_function_name(self):
        code = "def add(a, b):\n    return a + b"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert result["passed"] == 0
        assert "solve" in result["output_log"].lower()

    def test_empty_code(self):
        result = run_student_code("", BASIC_TEST_CASES)

        assert result["passed"] == 0


class TestRuntimeErrors:

    def test_division_by_zero(self):
        code = "def solve(a, b):\n    return a / 0"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert result["passed"] == 0
        assert "Error" in result["output_log"]

    def test_type_error(self):
        code = "def solve(a, b):\n    return 'not a number' + a"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert result["passed"] == 0


class TestPrintCapture:

    def test_print_output_is_captured(self):
        code = "def solve(a, b):\n    print('debug')\n    return a + b"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert result["passed"] == 2
        assert "debug" in result["output_log"]


class TestReturnStructure:

    def test_result_has_required_keys(self):
        code = "def solve(a, b):\n    return a + b"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert "output_log" in result
        assert "passed" in result
        assert "total" in result

    def test_total_matches_test_cases_count(self):
        code = "def solve(a, b):\n    return a + b"
        result = run_student_code(code, BASIC_TEST_CASES)

        assert result["total"] == len(BASIC_TEST_CASES)
