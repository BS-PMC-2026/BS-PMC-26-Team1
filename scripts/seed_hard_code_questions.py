"""
Adds a curated set of *harder* Python code-writing challenges to the bank.
Each is designed so the student should also be able to write meaningful
unit tests for their own solution afterwards.

Idempotent — re-running will not duplicate rows.

Usage:
    python scripts/seed_hard_code_questions.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.models import Module, Question, User, db  # noqa: E402
from app.services.code_runner_service import (  # noqa: E402
    default_compiler_label,
    default_environment_label,
    normalize_language,
)


HARD_QUESTIONS = [
    {
        "q": "Write `solve(a, b)` that returns the factorial of `a` plus the factorial of `b`. Assume 0 ≤ a, b ≤ 10.",
        "starter": (
            "def solve(a, b):\n"
            "    # factorial(a) + factorial(b)\n"
            "    pass\n"
        ),
        "tests": [
            {"inputs": [0, 0], "expected": 2},
            {"inputs": [3, 4], "expected": 30},
            {"inputs": [5, 5], "expected": 240},
            {"inputs": [10, 0], "expected": 3628801},
        ],
        "explanation": "Iteratively multiply 1..n for each argument and return the sum.",
        "difficulty": "hard",
    },
    {
        "q": "Write `solve(a, b)` that returns 1 if `a` is a prime number AND `b` is a prime number, otherwise 0. Assume positive integers.",
        "starter": (
            "def solve(a, b):\n"
            "    # both primes -> 1 else 0\n"
            "    pass\n"
        ),
        "tests": [
            {"inputs": [2, 3], "expected": 1},
            {"inputs": [4, 7], "expected": 0},
            {"inputs": [11, 13], "expected": 1},
            {"inputs": [1, 2], "expected": 0},
            {"inputs": [29, 31], "expected": 1},
        ],
        "explanation": "Implement an `is_prime(n)` helper and combine.",
        "difficulty": "hard",
    },
    {
        "q": "Write `solve(a, b)` that returns the nth Fibonacci number where n = a + b. F(0)=0, F(1)=1.",
        "starter": (
            "def solve(a, b):\n"
            "    n = a + b\n"
            "    # return Fibonacci(n)\n"
            "    pass\n"
        ),
        "tests": [
            {"inputs": [0, 0], "expected": 0},
            {"inputs": [1, 0], "expected": 1},
            {"inputs": [3, 2], "expected": 5},
            {"inputs": [5, 5], "expected": 55},
            {"inputs": [10, 0], "expected": 55},
        ],
        "explanation": "Use iterative Fibonacci with two rolling variables.",
        "difficulty": "hard",
    },
    {
        "q": "Write `solve(a, b)` that returns the number of digits shared between `a` and `b` (counted once per shared digit). Assume non-negative integers.",
        "starter": (
            "def solve(a, b):\n"
            "    # len(set(str(a)) & set(str(b)))\n"
            "    pass\n"
        ),
        "tests": [
            {"inputs": [123, 132], "expected": 3},
            {"inputs": [100, 200], "expected": 1},
            {"inputs": [12345, 67890], "expected": 0},
            {"inputs": [987, 789], "expected": 3},
        ],
        "explanation": "Convert to strings, take set intersection, return size.",
        "difficulty": "hard",
    },
    {
        "q": "Write `solve(a, b)` that returns the number of times digit `b` appears in integer `a`. Assume a ≥ 0 and 0 ≤ b ≤ 9.",
        "starter": (
            "def solve(a, b):\n"
            "    # count occurrences of digit b in number a\n"
            "    pass\n"
        ),
        "tests": [
            {"inputs": [11211, 1], "expected": 4},
            {"inputs": [123456, 0], "expected": 0},
            {"inputs": [0, 0], "expected": 1},
            {"inputs": [999, 9], "expected": 3},
            {"inputs": [102030, 0], "expected": 3},
        ],
        "explanation": "Iterate through `str(a)` and count characters equal to `str(b)`.",
        "difficulty": "hard",
    },
    {
        "q": "Write `solve(a, b)` that returns the digital root of `a + b`. The digital root sums digits repeatedly until one digit remains.",
        "starter": (
            "def solve(a, b):\n"
            "    n = a + b\n"
            "    # keep summing digits until single digit\n"
            "    pass\n"
        ),
        "tests": [
            {"inputs": [9, 0], "expected": 9},
            {"inputs": [38, 0], "expected": 2},
            {"inputs": [199, 1], "expected": 2},
            {"inputs": [9999, 1], "expected": 1},
        ],
        "explanation": "Loop while n >= 10, replace n with sum of its digits.",
        "difficulty": "hard",
    },
    {
        "q": "Write `solve(a, b)` that returns 1 if `a` and `b` are anagrams of each other (as strings of digits), else 0.",
        "starter": (
            "def solve(a, b):\n"
            "    # compare sorted digit strings\n"
            "    pass\n"
        ),
        "tests": [
            {"inputs": [123, 321], "expected": 1},
            {"inputs": [112, 121], "expected": 1},
            {"inputs": [123, 124], "expected": 0},
            {"inputs": [1001, 100], "expected": 0},
            {"inputs": [1, 1], "expected": 1},
        ],
        "explanation": "Use `sorted(str(a)) == sorted(str(b))`.",
        "difficulty": "hard",
    },
    {
        "q": "Write `solve(a, b)` that returns the smallest positive integer that is divisible by BOTH `a` and `b` (the LCM). Assume positive integers.",
        "starter": (
            "def solve(a, b):\n"
            "    # lcm(a, b) = a * b // gcd(a, b)\n"
            "    pass\n"
        ),
        "tests": [
            {"inputs": [4, 6], "expected": 12},
            {"inputs": [3, 5], "expected": 15},
            {"inputs": [12, 18], "expected": 36},
            {"inputs": [7, 1], "expected": 7},
        ],
        "explanation": "Compute GCD with Euclid, then a*b//gcd.",
        "difficulty": "hard",
    },
    {
        "q": "Write `solve(a, b)` that returns the number of integers between `a` and `b` inclusive (a ≤ b) that are perfect squares.",
        "starter": (
            "def solve(a, b):\n"
            "    # count k where k*k in [a, b]\n"
            "    pass\n"
        ),
        "tests": [
            {"inputs": [1, 10], "expected": 3},
            {"inputs": [16, 25], "expected": 2},
            {"inputs": [0, 0], "expected": 1},
            {"inputs": [50, 100], "expected": 3},
            {"inputs": [2, 3], "expected": 0},
        ],
        "explanation": "Iterate k from 0 upward, count when k*k is in [a, b].",
        "difficulty": "hard",
    },
    {
        "q": "Write `solve(a, b)` that returns the sum of all divisors of `a + b` (including 1 and a+b itself). Assume positive sum.",
        "starter": (
            "def solve(a, b):\n"
            "    n = a + b\n"
            "    # sum k for k in 1..n if n % k == 0\n"
            "    pass\n"
        ),
        "tests": [
            {"inputs": [3, 3], "expected": 12},
            {"inputs": [5, 5], "expected": 18},
            {"inputs": [4, 4], "expected": 15},
            {"inputs": [11, 1], "expected": 28},
            {"inputs": [1, 0], "expected": 1},
        ],
        "explanation": "Loop k=1..n adding k when divisible. Faster: only up to sqrt(n).",
        "difficulty": "hard",
    },
]


def run() -> dict:
    app = create_app()
    with app.app_context():
        exercise = Module.query.filter(Module.name.ilike("exercise")).first()
        if not exercise:
            raise RuntimeError("Exercise module missing.")
        author = User.query.filter_by(role="lecturer").first() or User.query.filter_by(role="admin").first()
        author_id = author.id if author else None

        existing = {q.question_text for q in Question.query.all()}
        added = 0
        lang = normalize_language("python")
        for data in HARD_QUESTIONS:
            if data["q"] in existing:
                continue
            db.session.add(
                Question(
                    question_text=data["q"],
                    question_type="code",
                    options_json=json.dumps([]),
                    correct_answer="def solve(a, b):",
                    explanation=data["explanation"],
                    difficulty=data["difficulty"],
                    module_id=exercise.id,
                    starter_code=data["starter"],
                    test_cases_json=json.dumps(data["tests"]),
                    language=lang,
                    execution_environment=default_environment_label(lang),
                    compiler_info=default_compiler_label(lang),
                    created_by=author_id,
                    is_active=True,
                )
            )
            existing.add(data["q"])
            added += 1
        db.session.commit()
        return {"added": added, "total_code_questions": Question.query.filter_by(question_type="code").count()}


if __name__ == "__main__":
    summary = run()
    print("Hard code questions seed complete:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
