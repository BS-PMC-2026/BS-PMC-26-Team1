import enum

class QuestionType(enum.Enum):
    MCQ = "mcq"
    CODE = "code"

def get_seed_questions():
    """
    Simulates database or static seed data providing two basic question formats.
    """
    return [
        {
            "id": 1,
            "type": QuestionType.MCQ.value,
            "title": "CI/CD Concepts",
            "content": "Which stage builds the application code?",
            "expected_answer": "Build",
            "options": ["Code", "Build", "Deploy"]
        },
        {
            "id": 2,
            "type": QuestionType.CODE.value,
            "title": "Basic Python Function",
            "content": "Write a function solve(a, b) that returns their sum.",
            "starter_code": "def solve(a, b):\n    # Write your code here\n    pass",
            "expected_answer": "def solve(a, b):", # basic substring validation placeholder
            "test_cases_count": 3
        }
    ]
