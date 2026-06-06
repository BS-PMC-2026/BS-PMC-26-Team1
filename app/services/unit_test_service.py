"""
Run a student's own unit-test suite against their solution.

The student writes a `tests()` function with `assert` statements. We:
  1. Validate they wrote at least one assertion (so they cannot trivially pass).
  2. Combine their solution + their test code in the same isolated sandbox.
  3. Execute `tests()` and report success / failure.

The sandbox limits and import restrictions are the same as the regular code
runner.
"""

from __future__ import annotations

import ast
import io
import sys
import threading
from typing import Any, Dict, Optional

from app.services.code_runner_service import (
    EXECUTION_RULES,
    _validate_python_imports,
)


def _count_assertions(code: str) -> int:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.Assert))


def _safe_env() -> Dict[str, Any]:
    return {
        "__builtins__": {
            "len": len,
            "print": print,
            "range": range,
            "int": int,
            "str": str,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "sorted": sorted,
            "reversed": reversed,
            "any": any,
            "all": all,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "AssertionError": AssertionError,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "IndexError": IndexError,
            "KeyError": KeyError,
        }
    }


def _run_combined(solution: str, tests: str, return_dict: dict) -> None:
    env = _safe_env()
    log_lines = []
    try:
        exec(solution, env)
    except Exception as e:
        return_dict["passed"] = False
        return_dict["assertions"] = 0
        return_dict["output_log"] = f"Solution failed to load:\n{e}"
        return

    try:
        exec(tests, env)
    except Exception as e:
        return_dict["passed"] = False
        return_dict["assertions"] = 0
        return_dict["output_log"] = f"Test code failed to load:\n{e}"
        return

    if "tests" not in env or not callable(env["tests"]):
        return_dict["passed"] = False
        return_dict["assertions"] = 0
        return_dict["output_log"] = (
            "Could not find a `tests()` function. Wrap your assertions in `def tests():`."
        )
        return

    captured = io.StringIO()
    sys.stdout = captured
    try:
        env["tests"]()
        log_lines.append("✓ All assertions passed.")
        return_dict["passed"] = True
    except AssertionError as e:
        message = str(e) or "(no message)"
        log_lines.append(f"✗ Assertion failed: {message}")
        return_dict["passed"] = False
    except Exception as e:
        log_lines.append(f"✗ Runtime error while running tests(): {type(e).__name__}: {e}")
        return_dict["passed"] = False
    finally:
        sys.stdout = sys.__stdout__

    extra = captured.getvalue().strip()
    if extra:
        log_lines.append("\n[Print output from your tests]\n" + extra)

    return_dict["output_log"] = "\n".join(log_lines)


def run_student_unit_test(
    solution_code: Optional[str],
    test_code: Optional[str],
    language: str = "python",
) -> Dict[str, Any]:
    solution_code = solution_code or ""
    test_code = test_code or ""

    if not solution_code.strip():
        return {
            "passed": False,
            "assertions": 0,
            "output_log": "You must submit a solution before writing unit tests.",
        }
    if not test_code.strip():
        return {
            "passed": False,
            "assertions": 0,
            "output_log": "Write at least one assertion inside a `tests()` function.",
        }

    assertions = _count_assertions(test_code)
    if assertions < 1:
        return {
            "passed": False,
            "assertions": 0,
            "output_log": (
                "We could not find any `assert` statement in your unit tests. "
                "Add at least one assertion inside `def tests():`."
            ),
        }

    rules = EXECUTION_RULES.get(language, EXECUTION_RULES.get("python", {}))
    max_bytes = int(rules.get("max_code_bytes", 100_000))
    if len((solution_code + test_code).encode("utf-8", errors="replace")) > max_bytes:
        return {
            "passed": False,
            "assertions": assertions,
            "output_log": f"Combined code too large (limit {max_bytes} bytes).",
        }

    imp_err = _validate_python_imports(solution_code) or _validate_python_imports(test_code)
    if imp_err:
        return {"passed": False, "assertions": assertions, "output_log": imp_err}

    time_limit = float(rules.get("time_limit_sec", 2.0))
    return_dict: Dict[str, Any] = {}

    def _target() -> None:
        try:
            _run_combined(solution_code, test_code, return_dict)
        except Exception as e:
            return_dict["passed"] = False
            return_dict["output_log"] = f"Internal runner error: {e}"

    t = threading.Thread(target=_target)
    t.daemon = True
    t.start()
    t.join(timeout=time_limit)

    if t.is_alive():
        return {
            "passed": False,
            "assertions": assertions,
            "output_log": f"Timeout: tests took longer than {time_limit}s.",
        }

    return_dict.setdefault("passed", False)
    return_dict.setdefault("output_log", "Unknown runner error.")
    return_dict["assertions"] = assertions
    return return_dict
