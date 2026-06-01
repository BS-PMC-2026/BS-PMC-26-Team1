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


def _seed_default_admin():
    from werkzeug.security import generate_password_hash

    from app.models import AdminProfile, User, db

    admin = User.query.filter_by(role="admin").first()
    if admin:
        return admin

    admin_email = "admin@ante.local"
    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        existing.role = "admin"
        existing.is_active = True
        db.session.flush()
        admin_user = existing
    else:
        admin_user = User(
            username="admin",
            full_name="System Administrator",
            email=admin_email,
            password_hash=generate_password_hash("Admin#12345"),
            role="admin",
            is_active=True,
        )
        db.session.add(admin_user)
        db.session.flush()

    profile = AdminProfile.query.filter_by(user_id=admin_user.id).first()
    if not profile:
        db.session.add(
            AdminProfile(user_id=admin_user.id, admin_id="ADMIN-001", scope="full")
        )
    return admin_user


def bootstrap_database():
    """
    Initializes modules and question bank records if they do not exist.
    Safe to call multiple times.
    """
    from app.models import Module, Question, TheoryContent, User, db
    from app.services.code_runner_service import (
        default_compiler_label,
        default_environment_label,
        normalize_language,
    )
    from app.services.settings_service import ensure_defaults

    ensure_defaults()
    _seed_default_admin()

    modules_map = {}
    for module_data in get_seed_modules():
        module = Module.query.filter_by(name=module_data["name"]).first()
        if not module:
            module = Module(**module_data)
            db.session.add(module)
            db.session.flush()
        modules_map[module.name.lower()] = module

    lecturer = User.query.filter_by(role="lecturer").first()
    created_by = lecturer.id if lecturer else None

    question_count = Question.query.count()
    for module in modules_map.values():
        if module.name.lower() not in {"intro", "pipeline"}:
            continue
        existing_theory = TheoryContent.query.filter_by(module_id=module.id).first()
        if not existing_theory:
            default_explanation = (
                "Core foundations that students should understand before progressing."
                if module.name.lower() == "intro"
                else "Stage-by-stage operational flow from commit to production."
            )
            default_examples = (
                "Example: small feature branch merged with CI checks before release."
                if module.name.lower() == "intro"
                else "Example: Code -> Build -> Test -> Deploy with automated quality gates."
            )
            db.session.add(
                TheoryContent(
                    module_id=module.id,
                    headline=f"{module.name} Theory Highlights",
                    explanation=default_explanation,
                    examples=default_examples,
                    updated_by=created_by,
                )
            )

    if question_count > 0:
        db.session.commit()
        return

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

        code_lang = normalize_language("python")
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
            language=code_lang if q["type"] == QuestionType.CODE.value else None,
            execution_environment=(
                default_environment_label(code_lang) if q["type"] == QuestionType.CODE.value else None
            ),
            compiler_info=(
                default_compiler_label(code_lang) if q["type"] == QuestionType.CODE.value else None
            ),
            is_active=True,
            created_by=created_by,
        )
        db.session.add(question_row)

    db.session.commit()

