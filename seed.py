import enum
import json

class QuestionType(enum.Enum):
    MCQ = "mcq"
    CODE = "code"
    OPEN = "open"

def get_seed_questions():
    return [
        {
            "id": 1,
            "type": QuestionType.MCQ.value,
            "title": "CI/CD Concepts",
            "content": "Which stage builds the application code?",
            "expected_answer": "Build",
            "options": ["Code", "Build", "Deploy"],
            "explanation": "The 'Build' stage compiles source code, resolves dependencies, and created an executable artifact."
        },
        {
            "id": 2,
            "type": QuestionType.CODE.value,
            "title": "Basic Python Function",
            "content": "Write a function solve(a, b) that returns their sum.",
            "starter_code": "def solve(a, b):\n    # Write your code here\n    pass",
            "expected_answer": "def solve(a, b):", # basic substring validation placeholder
            "test_cases_count": 3,
            "explanation": "A python function named 'solve' taking two parameters 'a' and 'b', returning 'a + b'."
        },
        {
            "id": 3,
            "type": QuestionType.MCQ.value,
            "title": "Continuous Deployment",
            "content": "What is the primary difference between Continuous Delivery and Continuous Deployment?",
            "expected_answer": "Automated release without manual approval",
            "options": ["Faster automated tests", "Automated release without manual approval", "No code reviews are needed"],
            "explanation": "Continuous Deployment pushes all passing changes automatically to production without manual intervention."
        },
        {
            "id": 4,
            "type": QuestionType.MCQ.value,
            "title": "Test Coverage",
            "content": "Why is testing important in CI/CD?",
            "expected_answer": "To ensure changes don't break existing features",
            "options": ["To increase build time", "To ensure changes don't break existing features", "To automatically generate documentation"],
            "explanation": "Automated testing guarantees that code integrating into the main branch continues to function correctly."
        }
    ]


def get_seed_modules():
    return [
        {
            "name": "Intro",
            "description": "CI/CD fundamentals and practical benefits.",
            "display_order": 1,
            "route": "/intro",
        },
        {
            "name": "Pipeline",
            "description": "Interactive CI/CD pipeline stages.",
            "display_order": 2,
            "route": "/pipeline",
        },
        {
            "name": "Exercise",
            "description": "Hands-on mixed question practice.",
            "display_order": 3,
            "route": "/exercise",
        },
    ]


def bootstrap_database():
    """
    Initializes modules and question bank records if they do not exist.
    Safe to call multiple times.
    """
    from app.models import Module, Question, User, db

    modules_map = {}
    for module_data in get_seed_modules():
        module = Module.query.filter_by(name=module_data["name"]).first()
        if not module:
            module = Module(**module_data)
            db.session.add(module)
            db.session.flush()
        modules_map[module.name.lower()] = module

    question_count = Question.query.count()
    if question_count > 0:
        db.session.commit()
        return

    lecturer = User.query.filter_by(role="lecturer").first()
    created_by = lecturer.id if lecturer else None
    exercise_module = modules_map.get("exercise")
    if not exercise_module:
        db.session.commit()
        return

    for q in get_seed_questions():
        starter_code = q.get("starter_code")
        test_cases = None
        if q["type"] == QuestionType.CODE.value:
            test_cases = [
                {"inputs": [2, 3], "expected": 5},
                {"inputs": [-1, 1], "expected": 0},
                {"inputs": [10, 20], "expected": 30},
            ]

        question_row = Question(
            id=q["id"],
            question_text=q["content"],
            question_type=q["type"],
            options_json=json.dumps(q.get("options", [])),
            correct_answer=q["expected_answer"],
            explanation=q["explanation"],
            difficulty="easy" if q["id"] < 3 else "medium",
            module_id=exercise_module.id,
            starter_code=starter_code,
            test_cases_json=json.dumps(test_cases) if test_cases else None,
            is_active=True,
            created_by=created_by,
        )
        db.session.add(question_row)

    db.session.commit()

