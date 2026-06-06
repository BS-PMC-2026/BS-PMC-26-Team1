import io
import re
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

# Supported runtimes for student code execution (extend here as engines are added).
SUPPORTED_LANGUAGES = frozenset({"python"})

# Execution rules per language key (after normalize_language).
EXECUTION_RULES: Dict[str, Dict[str, Any]] = {
    "python": {
        "engine": "builtin_exec_thread_isolated",
        "time_limit_sec": 2.0,
        "memory_limit_mb": 128,
        "max_code_bytes": 100_000,
        "restricted_import_roots": frozenset(
            {
                "os",
                "subprocess",
                "socket",
                "shutil",
                "pathlib",
                "importlib",
                "ctypes",
                "sys",
                "multiprocessing",
            }
        ),
    },
}

_DEFAULT_ENVIRONMENT_LABEL = "Secure sandbox execution"


def normalize_language(language: Optional[str]) -> str:
    if not language or not str(language).strip():
        return "python"
    lang = str(language).strip().lower()
    aliases = {"py": "python", "js": "javascript", "node": "javascript", "nodejs": "javascript"}
    return aliases.get(lang, lang)


def default_environment_label(language: Optional[str] = None) -> str:
    return _DEFAULT_ENVIRONMENT_LABEL


def default_compiler_label(language: Optional[str] = None) -> str:
    lang = normalize_language(language)
    if lang == "python":
        v = sys.version_info
        return f"Python {v.major}.{v.minor}.{v.micro}"
    return f"Runtime for {lang} (not available locally)"


def execution_engine_for_language(language: Optional[str]) -> str:
    lang = normalize_language(language)
    if lang in SUPPORTED_LANGUAGES and lang in EXECUTION_RULES:
        return str(EXECUTION_RULES[lang]["engine"])
    return "unsupported"


def _rules_for_language(language: Optional[str]) -> Optional[Dict[str, Any]]:
    lang = normalize_language(language)
    if lang not in SUPPORTED_LANGUAGES:
        return None
    return EXECUTION_RULES.get(lang)


def _validate_python_imports(code: str) -> Optional[str]:
    rules = EXECUTION_RULES.get("python")
    if not rules:
        return None
    forbidden = rules["restricted_import_roots"]
    import_line = re.compile(
        r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.,\s]+))\s*",
        re.IGNORECASE | re.MULTILINE,
    )
    for line in code.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = import_line.match(line)
        if not m:
            continue
        if m.group(1):
            root = m.group(1).split(".")[0].lower()
            if root in forbidden:
                return f"Restricted import blocked: '{root}' is not allowed in this environment."
        if m.group(2):
            for part in m.group(2).split(","):
                name = part.strip().split()[0].split(".")[0].lower() if part.strip() else ""
                if name and name in forbidden:
                    return f"Restricted import blocked: '{name}' is not allowed in this environment."
    if "__import__" in code:
        return "Use of __import__ is not allowed in this environment."
    return None


def _run_isolated(code: str, test_cases: List[dict], return_dict: dict) -> None:
    safe_env = {
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
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
        }
    }

    try:
        exec(code, safe_env)
    except Exception as e:
        return_dict["error"] = True
        return_dict["output_log"] = f"Syntax/Compile Error:\n{str(e)}"
        return_dict["passed"] = 0
        return

    if "solve" not in safe_env:
        return_dict["error"] = True
        return_dict["output_log"] = (
            "Error: Could not find function 'solve(a, b)'. Did you rename it?"
        )
        return_dict["passed"] = 0
        return

    solve_func = safe_env["solve"]
    passed_count = 0
    output_log_lines = []

    for i, tc in enumerate(test_cases):
        inputs = tc.get("inputs", [])
        expected = tc.get("expected", None)

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            result = solve_func(*inputs)
            printed = captured_output.getvalue()

            if result == expected:
                passed_count += 1
                output_log_lines.append(
                    f"Test {i+1} Passed | Inputs: {inputs} -> Got: {result}"
                )
            else:
                output_log_lines.append(
                    f"Test {i+1} Failed | Inputs: {inputs} -> Expected: {expected}, Got: {result}"
                )

            if printed:
                output_log_lines.append(f"  [Prints]: {printed.strip()}")

        except Exception as e:
            output_log_lines.append(f"Test {i+1} Runtime Error: {str(e)}")
        finally:
            sys.stdout = sys.__stdout__

    return_dict["error"] = False
    return_dict["output_log"] = "\n".join(output_log_lines)
    return_dict["passed"] = passed_count


def run_student_code(
    code: Optional[str],
    test_cases: Optional[List[dict]],
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run student code for the given language using the mapped execution engine.
    Unsupported languages and validation failures return a safe log without raising.
    """
    lang = normalize_language(language)
    cases: List[dict] = list(test_cases) if test_cases else []

    try:
        code_str = "" if code is None else str(code)
    except Exception:
        code_str = ""

    if lang not in SUPPORTED_LANGUAGES:
        return {
            "output_log": (
                f"Unsupported language '{lang}'. "
                f"Supported in this environment: {', '.join(sorted(SUPPORTED_LANGUAGES))}."
            ),
            "passed": 0,
            "total": len(cases),
        }

    rules = _rules_for_language(lang)
    if not rules:
        return {
            "output_log": f"Execution is not configured for language '{lang}'.",
            "passed": 0,
            "total": len(cases),
        }

    max_bytes = int(rules.get("max_code_bytes", 100_000))
    if len(code_str.encode("utf-8", errors="replace")) > max_bytes:
        return {
            "output_log": (
                f"Code rejected: exceeds maximum size ({max_bytes} bytes). "
                "Shorten your submission and try again."
            ),
            "passed": 0,
            "total": len(cases),
        }

    if lang == "python":
        imp_err = _validate_python_imports(code_str)
        if imp_err:
            return {"output_log": imp_err, "passed": 0, "total": len(cases)}

    time_limit = float(rules.get("time_limit_sec", 2.0))
    return_dict: Dict[str, Any] = {}

    def _target() -> None:
        try:
            _run_isolated(code_str, cases, return_dict)
        except Exception as e:
            return_dict["error"] = True
            return_dict["output_log"] = f"Internal runner error (safe): {str(e)}"
            return_dict["passed"] = 0

    t = threading.Thread(target=_target)
    t.daemon = True
    t.start()
    t.join(timeout=time_limit)

    if t.is_alive():
        return {
            "output_log": (
                f"Timeout Error: Code execution took longer than {time_limit} seconds. "
                "Possible infinite loop."
            ),
            "passed": 0,
            "total": len(cases),
        }

    return {
        "output_log": return_dict.get("output_log", "Unknown Error"),
        "passed": return_dict.get("passed", 0),
        "total": len(cases),
    }


def execution_rules_summary(language: Optional[str]) -> Tuple[str, str, str]:
    """Human-readable limits for UI or logging."""
    lang = normalize_language(language)
    rules = _rules_for_language(lang)
    if not rules:
        return ("n/a", "n/a", "n/a")
    mem = rules.get("memory_limit_mb", "n/a")
    t = rules.get("time_limit_sec", "n/a")
    return (
        f"time_limit_sec={t}",
        f"memory_limit_mb={mem}",
        f"restricted_imports={'yes' if lang == 'python' else 'n/a'}",
    )
