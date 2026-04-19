from app.seed import QuestionType


def check_answer(
    user_answer,
    expected_answer,
    explanation="",
    question_type=QuestionType.MCQ.value,
    total_tests=3,
    test_cases=None,
):
    """
    Reusable feedback service.
    Supports both MCQ and Code evaluation modes.
    Returns whether the answer is correct, an explanation, and passed test counts (for code).
    """
    if not user_answer or not expected_answer:
        return {
            "status": "Incorrect",
            "is_correct": False,
            "explanation": "Answer cannot be empty.",
            "passed_test_count": 0,
            "raw_runner_output": "",
            "score": 0,
        }

    is_correct = False
    passed_tests = 0
    score = 0
    run_results = {"output_log": ""}

    if question_type == QuestionType.MCQ.value:
        is_correct = user_answer.strip().lower() == expected_answer.strip().lower()
        if is_correct:
            explanation = f"Great job. '{user_answer}' is correct. {explanation}".strip()
            score = 100
        else:
            explanation = (
                f"Your answer '{user_answer}' is not correct. "
                f"The correct answer is '{expected_answer}'. {explanation}"
            ).strip()
            score = 0

    elif question_type == QuestionType.OPEN.value:
        normalized_answer = user_answer.strip().lower()
        expected_variants = [variant.strip().lower() for variant in str(expected_answer).split("|") if variant.strip()]
        is_correct = any(variant in normalized_answer for variant in expected_variants) if expected_variants else False
        if is_correct:
            explanation = f"Good reflection. {explanation}".strip()
            score = 100
        else:
            explanation = (
                "Your response needs stronger alignment with the expected concept. "
                f"Hint keywords: {', '.join(expected_variants)}. {explanation}"
            ).strip()
            score = 40 if len(normalized_answer.split()) >= 8 else 0

    elif question_type == QuestionType.CODE.value:
        from app.services.code_runner_service import run_student_code
        
        mock_test_cases = test_cases if test_cases else [
            {"inputs": [2, 3], "expected": 5},
            {"inputs": [-1, 1], "expected": 0},
            {"inputs": [10, 20], "expected": 30},
        ]
        
        run_results = run_student_code(user_answer, mock_test_cases)
        
        if run_results["passed"] == len(mock_test_cases):
            is_correct = True
        else:
            is_correct = False
            
        passed_tests = run_results["passed"]
        score = int((passed_tests / len(mock_test_cases)) * 100) if mock_test_cases else 0
        
        # Override explanation to include test-by-test traces.
        if is_correct:
            explanation = (
                f"All tests passed ({passed_tests}/{len(mock_test_cases)}). "
                "Your implementation behaves as expected.\n\n"
                f"{run_results['output_log']}"
            )
        else:
            explanation = (
                f"Passed {passed_tests}/{len(mock_test_cases)} tests. "
                "Review failed cases below and adjust your logic.\n\n"
                f"{run_results['output_log']}"
            )

    feedback = "Correct" if is_correct else "Incorrect"
    
    return {
        "status": feedback,
        "is_correct": is_correct,
        "explanation": explanation if explanation else "Please review the material and try again.",
        "passed_test_count": passed_tests,
        "raw_runner_output": run_results["output_log"] if question_type == QuestionType.CODE.value else "",
        "score": score,
    }
