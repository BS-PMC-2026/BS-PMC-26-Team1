"""Tests for seed data and QuestionType enum."""

from app.seed import get_seed_questions, QuestionType


class TestQuestionTypeEnum:

    def test_mcq_value(self):
        assert QuestionType.MCQ.value == "mcq"

    def test_code_value(self):
        assert QuestionType.CODE.value == "code"


class TestGetSeedQuestions:

    def test_returns_list(self):
        questions = get_seed_questions()
        assert isinstance(questions, list)

    def test_returns_correct_count(self):
        questions = get_seed_questions()
        assert len(questions) >= 4

    def test_mcq_question_has_required_fields(self):
        questions = get_seed_questions()
        mcq = questions[0]

        assert mcq["type"] == QuestionType.MCQ.value
        assert "id" in mcq
        assert "title" in mcq
        assert "content" in mcq
        assert "expected_answer" in mcq
        assert "options" in mcq
        assert isinstance(mcq["options"], list)
        assert len(mcq["options"]) > 0

    def test_code_question_has_required_fields(self):
        questions = get_seed_questions()
        code_q = questions[1]

        assert code_q["type"] == QuestionType.CODE.value
        assert "id" in code_q
        assert "title" in code_q
        assert "content" in code_q
        assert "expected_answer" in code_q
        assert "starter_code" in code_q

    def test_question_ids_are_unique(self):
        questions = get_seed_questions()
        ids = [q["id"] for q in questions]
        assert len(ids) == len(set(ids))
