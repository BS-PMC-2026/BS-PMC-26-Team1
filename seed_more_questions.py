"""
Seed a large additional question bank into the Exercise module.
Mix of MCQ, OPEN, and CODE questions covering CI/CD, DevOps, Git, Docker,
testing, and Python basics. Idempotent — re-running does not duplicate rows.

Usage:
    python scripts/seed_more_questions.py
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


# ----- MCQ ------------------------------------------------------------------
MCQ_QUESTIONS = [
    {
        "q": "Which Git command creates a new branch and switches to it?",
        "a": "git checkout -b feature",
        "options": ["git branch feature", "git checkout -b feature", "git switch feature"],
        "explanation": "`git checkout -b NAME` is a shortcut to create a new branch and switch to it in one step.",
        "difficulty": "easy",
    },
    {
        "q": "What does `git pull` do?",
        "a": "Fetches and merges changes from the remote",
        "options": [
            "Pushes local changes to the remote",
            "Fetches and merges changes from the remote",
            "Deletes the working copy",
        ],
        "explanation": "`git pull` is equivalent to `git fetch` followed by `git merge` on the tracked branch.",
        "difficulty": "easy",
    },
    {
        "q": "What is a Dockerfile?",
        "a": "A text file with instructions to build a container image",
        "options": [
            "A binary container image",
            "A text file with instructions to build a container image",
            "A networking configuration for Docker Swarm",
        ],
        "explanation": "Dockerfiles describe, step by step, how to assemble a container image.",
        "difficulty": "easy",
    },
    {
        "q": "Which command lists running Docker containers?",
        "a": "docker ps",
        "options": ["docker ls", "docker ps", "docker images"],
        "explanation": "`docker ps` lists running containers; `docker ps -a` adds stopped ones.",
        "difficulty": "easy",
    },
    {
        "q": "What does CI primarily try to prevent?",
        "a": "Long-lived divergent branches and integration pain",
        "options": [
            "Compilers becoming faster",
            "Long-lived divergent branches and integration pain",
            "Developers writing tests",
        ],
        "explanation": "Continuous Integration avoids 'merge hell' by integrating small changes frequently.",
        "difficulty": "medium",
    },
    {
        "q": "In a CI/CD pipeline, what is a 'green build'?",
        "a": "A build where all stages pass successfully",
        "options": [
            "A build using a green logo",
            "A build where all stages pass successfully",
            "A build that has not started yet",
        ],
        "explanation": "Green builds indicate every step (compile, test, lint, etc.) succeeded.",
        "difficulty": "easy",
    },
    {
        "q": "What is the main purpose of unit tests?",
        "a": "Verify a small piece of code in isolation",
        "options": [
            "Test the entire system end-to-end",
            "Verify a small piece of code in isolation",
            "Replace integration tests",
        ],
        "explanation": "Unit tests focus on a single unit (often one function or class) without external dependencies.",
        "difficulty": "easy",
    },
    {
        "q": "Which file commonly lists project dependencies in a Python project?",
        "a": "requirements.txt",
        "options": ["package.json", "requirements.txt", "Cargo.toml"],
        "explanation": "Python projects typically declare dependencies in `requirements.txt` or `pyproject.toml`.",
        "difficulty": "easy",
    },
    {
        "q": "What is the difference between `git merge` and `git rebase`?",
        "a": "Merge keeps history; rebase rewrites it onto another base",
        "options": [
            "They are identical",
            "Merge keeps history; rebase rewrites it onto another base",
            "Only merge can be undone",
        ],
        "explanation": "Merge preserves the actual branch topology; rebase replays commits on top of another branch.",
        "difficulty": "medium",
    },
    {
        "q": "What is 'infrastructure as code' (IaC)?",
        "a": "Managing infrastructure through version-controlled configuration files",
        "options": [
            "Writing application code on production servers",
            "Managing infrastructure through version-controlled configuration files",
            "Using only physical hardware",
        ],
        "explanation": "IaC tools (Terraform, Ansible, CloudFormation) treat infrastructure like software.",
        "difficulty": "medium",
    },
    {
        "q": "Which HTTP status code means 'Created'?",
        "a": "201",
        "options": ["200", "201", "204"],
        "explanation": "201 indicates the request succeeded and a new resource was created.",
        "difficulty": "easy",
    },
    {
        "q": "What is the goal of a code review?",
        "a": "Catch bugs, share knowledge, and improve code quality",
        "options": [
            "Slow down the team",
            "Catch bugs, share knowledge, and improve code quality",
            "Replace automated tests",
        ],
        "explanation": "Reviews build shared understanding, surface defects early, and raise overall quality.",
        "difficulty": "easy",
    },
    {
        "q": "What is a feature flag?",
        "a": "A toggle that enables/disables functionality at runtime",
        "options": [
            "A marketing banner",
            "A toggle that enables/disables functionality at runtime",
            "A type of unit test",
        ],
        "explanation": "Feature flags decouple deployment from release; code can ship dark and be turned on gradually.",
        "difficulty": "medium",
    },
    {
        "q": "Which testing pyramid layer is widest?",
        "a": "Unit tests",
        "options": ["End-to-end tests", "Integration tests", "Unit tests"],
        "explanation": "The pyramid suggests many fast unit tests at the base, fewer integration tests, and very few E2E.",
        "difficulty": "medium",
    },
    {
        "q": "Which command shows the current Git status?",
        "a": "git status",
        "options": ["git show", "git status", "git diff"],
        "explanation": "`git status` displays the state of the working tree and the staging area.",
        "difficulty": "easy",
    },
    {
        "q": "What is a 'blue-green deployment'?",
        "a": "Running two production environments and switching traffic between them",
        "options": [
            "A deployment done at night",
            "Running two production environments and switching traffic between them",
            "Deploying twice the same code",
        ],
        "explanation": "Blue/green keeps an idle copy ready so switching is instant and rollback is just flipping back.",
        "difficulty": "medium",
    },
    {
        "q": "What is canary deployment?",
        "a": "Releasing to a small subset of users first",
        "options": [
            "Releasing to every user at once",
            "Releasing to a small subset of users first",
            "Releasing only on weekends",
        ],
        "explanation": "Canary releases expose a small percentage of users to a new version to limit blast radius.",
        "difficulty": "medium",
    },
    {
        "q": "Which is NOT typically part of a CI pipeline?",
        "a": "Manual end-user UI screenshots",
        "options": [
            "Compile / build",
            "Manual end-user UI screenshots",
            "Run automated tests",
        ],
        "explanation": "CI pipelines automate work; ad-hoc manual screenshots are out of scope for a CI pipeline.",
        "difficulty": "easy",
    },
    {
        "q": "What is the role of a build artifact registry?",
        "a": "Store versioned build outputs for deployment",
        "options": [
            "Store user passwords",
            "Store versioned build outputs for deployment",
            "Replace source control",
        ],
        "explanation": "Registries keep build outputs (images, packages) versioned and available for promotion.",
        "difficulty": "medium",
    },
    {
        "q": "Which keyword in Python defines a function?",
        "a": "def",
        "options": ["function", "def", "fn"],
        "explanation": "`def` is Python's function-definition keyword.",
        "difficulty": "easy",
    },
    {
        "q": "What does TDD stand for?",
        "a": "Test-Driven Development",
        "options": [
            "Time-Driven Deployment",
            "Test-Driven Development",
            "Type-Driven Design",
        ],
        "explanation": "TDD = Test-Driven Development: write a failing test, make it pass, refactor.",
        "difficulty": "easy",
    },
    {
        "q": "Which Linux command prints the current working directory?",
        "a": "pwd",
        "options": ["pwd", "cwd", "dir"],
        "explanation": "`pwd` prints the working directory on Unix-like systems.",
        "difficulty": "easy",
    },
    {
        "q": "What does YAML stand for?",
        "a": "YAML Ain't Markup Language",
        "options": [
            "Yet Another Markup Language",
            "YAML Ain't Markup Language",
            "Young Application Markup Language",
        ],
        "explanation": "YAML's recursive acronym is 'YAML Ain't Markup Language'; it's a human-readable data format.",
        "difficulty": "medium",
    },
    {
        "q": "What is the purpose of a `.gitignore` file?",
        "a": "Tell Git which files to skip from version control",
        "options": [
            "Encrypt files in Git",
            "Tell Git which files to skip from version control",
            "Store Git authentication tokens",
        ],
        "explanation": "Paths and globs in `.gitignore` are excluded from Git tracking.",
        "difficulty": "easy",
    },
    {
        "q": "In Agile, what is a 'sprint'?",
        "a": "A fixed-length development iteration",
        "options": [
            "A fast Git command",
            "A fixed-length development iteration",
            "An emergency hotfix",
        ],
        "explanation": "Sprints are time-boxed iterations (often 1-4 weeks) where the team delivers an increment.",
        "difficulty": "easy",
    },
]

# ----- OPEN -----------------------------------------------------------------
OPEN_QUESTIONS = [
    {
        "q": "In your own words, what is the difference between Git and GitHub?",
        "a": "git|version control|local|distributed|github|remote|hosting|repository|cloud",
        "explanation": "Git is the distributed version-control system; GitHub is a hosting platform built on top of Git.",
        "difficulty": "easy",
    },
    {
        "q": "Why are automated tests important in CI/CD?",
        "a": "feedback|catch|bugs|regression|fast|early|confidence|prevent|quality",
        "explanation": "Automated tests give fast feedback, catch regressions early, and build the confidence needed to release often.",
        "difficulty": "easy",
    },
    {
        "q": "Explain what a 'pull request' is and why teams use them.",
        "a": "review|merge|branch|propose|change|collaboration|discuss|approve",
        "explanation": "A pull request proposes merging a branch and provides a place for review, discussion, and approval before integration.",
        "difficulty": "medium",
    },
    {
        "q": "What is the value of containers (like Docker) for development teams?",
        "a": "consistent|reproducible|portable|isolation|environment|dependencies|works on my machine|standard",
        "explanation": "Containers package code with its dependencies, eliminating 'works on my machine' issues and standardising environments.",
        "difficulty": "medium",
    },
    {
        "q": "Describe one risk of skipping code reviews and how CI/CD helps.",
        "a": "bug|defect|knowledge|silo|quality|automated|tests|lint|catch|prevent",
        "explanation": "Skipping reviews lets bugs and knowledge silos through; CI helps by automating tests and lint as a safety net.",
        "difficulty": "medium",
    },
    {
        "q": "Why do teams keep their main branch always deployable?",
        "a": "release|hotfix|production|safe|quickly|trust|confidence|deploy|stable",
        "explanation": "A deployable main allows fast hotfixes, safer releases, and builds trust in the change-delivery process.",
        "difficulty": "medium",
    },
    {
        "q": "Explain the concept of 'shift left' testing.",
        "a": "earlier|pipeline|prevent|bug|cost|developer|test|sooner|cheap",
        "explanation": "Shift-left means moving quality checks earlier in the pipeline so defects are cheaper to find and fix.",
        "difficulty": "medium",
    },
    {
        "q": "What is technical debt and how does it affect a CI/CD pipeline?",
        "a": "debt|shortcut|maintenance|slow|fragile|flaky|test|quality|cost|refactor",
        "explanation": "Technical debt is accumulated shortcut cost; it slows delivery and makes pipelines flakier over time.",
        "difficulty": "medium",
    },
    {
        "q": "Why are environment variables used for secrets instead of hard-coding them?",
        "a": "secret|secure|secret|leak|rotate|configuration|environment|safer|injection",
        "explanation": "Environment-injected secrets stay out of source control and can be rotated per environment without code changes.",
        "difficulty": "medium",
    },
    {
        "q": "Give a concrete example of when continuous deployment would NOT be appropriate.",
        "a": "regulated|medical|safety|critical|approval|manual|review|legal|compliance|finance",
        "explanation": "Highly regulated systems (medical, aviation, finance) often need manual approval gates that conflict with full continuous deployment.",
        "difficulty": "hard",
    },
]

# ----- CODE -----------------------------------------------------------------
CODE_QUESTIONS = [
    {
        "q": "Write `solve(a, b)` that returns a + b.",
        "starter": "def solve(a, b):\n    # return the sum\n    pass",
        "tests": [
            {"inputs": [1, 2], "expected": 3},
            {"inputs": [-5, 5], "expected": 0},
            {"inputs": [100, 250], "expected": 350},
        ],
        "explanation": "Just return `a + b`.",
        "difficulty": "easy",
    },
    {
        "q": "Write `solve(a, b)` that returns the product of a and b.",
        "starter": "def solve(a, b):\n    # return a * b\n    pass",
        "tests": [
            {"inputs": [3, 4], "expected": 12},
            {"inputs": [0, 99], "expected": 0},
            {"inputs": [-2, 5], "expected": -10},
        ],
        "explanation": "Return `a * b`.",
        "difficulty": "easy",
    },
    {
        "q": "Write `solve(a, b)` that returns the integer division of a by b. Assume b != 0.",
        "starter": "def solve(a, b):\n    # return a // b\n    pass",
        "tests": [
            {"inputs": [10, 3], "expected": 3},
            {"inputs": [20, 4], "expected": 5},
            {"inputs": [-7, 2], "expected": -4},
        ],
        "explanation": "Use `a // b` for integer division.",
        "difficulty": "easy",
    },
    {
        "q": "Write `solve(a, b)` that returns the remainder of a divided by b.",
        "starter": "def solve(a, b):\n    # return a % b\n    pass",
        "tests": [
            {"inputs": [10, 3], "expected": 1},
            {"inputs": [9, 3], "expected": 0},
            {"inputs": [7, 4], "expected": 3},
        ],
        "explanation": "Use the modulo operator `a % b`.",
        "difficulty": "easy",
    },
    {
        "q": "Write `solve(a, b)` that returns the minimum of a and b.",
        "starter": "def solve(a, b):\n    # return min(a, b)\n    pass",
        "tests": [
            {"inputs": [4, 9], "expected": 4},
            {"inputs": [-3, -10], "expected": -10},
            {"inputs": [7, 7], "expected": 7},
        ],
        "explanation": "Return `min(a, b)`.",
        "difficulty": "easy",
    },
    {
        "q": "Write `solve(a, b)` that returns a raised to the power b (integer b ≥ 0).",
        "starter": "def solve(a, b):\n    # return a ** b\n    pass",
        "tests": [
            {"inputs": [2, 3], "expected": 8},
            {"inputs": [5, 0], "expected": 1},
            {"inputs": [3, 4], "expected": 81},
        ],
        "explanation": "Use `a ** b` or a loop.",
        "difficulty": "medium",
    },
    {
        "q": "Write `solve(a, b)` that returns the greatest common divisor of a and b. Assume both positive.",
        "starter": "def solve(a, b):\n    # Euclidean algorithm\n    pass",
        "tests": [
            {"inputs": [12, 18], "expected": 6},
            {"inputs": [100, 75], "expected": 25},
            {"inputs": [17, 5], "expected": 1},
        ],
        "explanation": "Loop with `a, b = b, a % b` until b == 0; return a.",
        "difficulty": "medium",
    },
    {
        "q": "Write `solve(a, b)` that returns 1 if a is divisible by b, else 0.",
        "starter": "def solve(a, b):\n    # return 1 if a % b == 0 else 0\n    pass",
        "tests": [
            {"inputs": [10, 5], "expected": 1},
            {"inputs": [10, 3], "expected": 0},
            {"inputs": [0, 7], "expected": 1},
        ],
        "explanation": "Check divisibility with modulo and return an int.",
        "difficulty": "easy",
    },
    {
        "q": "Write `solve(a, b)` that returns the sum of all integers from a to b inclusive (a ≤ b).",
        "starter": "def solve(a, b):\n    # sum(range(a, b + 1))\n    pass",
        "tests": [
            {"inputs": [1, 5], "expected": 15},
            {"inputs": [0, 10], "expected": 55},
            {"inputs": [-2, 2], "expected": 0},
        ],
        "explanation": "Use `sum(range(a, b + 1))` or the arithmetic series formula.",
        "difficulty": "medium",
    },
    {
        "q": "Write `solve(a, b)` that returns the number of digits of a + b (a, b ≥ 0).",
        "starter": "def solve(a, b):\n    # return len(str(a + b))\n    pass",
        "tests": [
            {"inputs": [12, 34], "expected": 2},
            {"inputs": [100, 200], "expected": 3},
            {"inputs": [0, 0], "expected": 1},
        ],
        "explanation": "Convert the sum to string and take its length.",
        "difficulty": "medium",
    },
]


def _existing_question_texts() -> set:
    return {q.question_text for q in Question.query.all()}


def _insert_mcq(module: Module, author_id: int, existing: set) -> int:
    inserted = 0
    for data in MCQ_QUESTIONS:
        if data["q"] in existing:
            continue
        db.session.add(
            Question(
                question_text=data["q"],
                question_type="mcq",
                options_json=json.dumps(data["options"]),
                correct_answer=data["a"],
                explanation=data["explanation"],
                difficulty=data["difficulty"],
                module_id=module.id,
                created_by=author_id,
                is_active=True,
            )
        )
        existing.add(data["q"])
        inserted += 1
    return inserted


def _insert_open(module: Module, author_id: int, existing: set) -> int:
    inserted = 0
    for data in OPEN_QUESTIONS:
        if data["q"] in existing:
            continue
        db.session.add(
            Question(
                question_text=data["q"],
                question_type="open",
                options_json=json.dumps([]),
                correct_answer=data["a"],
                explanation=data["explanation"],
                difficulty=data["difficulty"],
                module_id=module.id,
                created_by=author_id,
                is_active=True,
            )
        )
        existing.add(data["q"])
        inserted += 1
    return inserted


def _insert_code(module: Module, author_id: int, existing: set) -> int:
    inserted = 0
    lang = normalize_language("python")
    for data in CODE_QUESTIONS:
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
                module_id=module.id,
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
        inserted += 1
    return inserted


def run() -> dict:
    app = create_app()
    with app.app_context():
        exercise = Module.query.filter(Module.name.ilike("exercise")).first()
        if not exercise:
            raise RuntimeError("Exercise module is missing. Boot the app once before seeding.")
        author = (
            User.query.filter_by(role="lecturer").first()
            or User.query.filter_by(role="admin").first()
        )
        author_id = author.id if author else None

        existing = _existing_question_texts()
        mcq_added = _insert_mcq(exercise, author_id, existing)
        open_added = _insert_open(exercise, author_id, existing)
        code_added = _insert_code(exercise, author_id, existing)
        db.session.commit()
        return {
            "mcq_added": mcq_added,
            "open_added": open_added,
            "code_added": code_added,
            "total_questions": Question.query.count(),
        }


if __name__ == "__main__":
    summary = run()
    print("Added questions:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
