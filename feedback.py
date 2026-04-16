from app.seed import QuestionType

def check_answer(user_answer, expected_answer, explanation="", question_type=QuestionType.MCQ.value, total_tests=3):
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
            "passed_test_count": 0
        }

    is_correct = False
    passed_tests = 0

    if question_type == QuestionType.MCQ.value:
        is_correct = user_answer.strip().lower() == expected_answer.strip().lower()
    
    elif question_type == QuestionType.CODE.value:
        from app.services.code_runner_service import run_student_code
        
        # Hardcoding the test_cases corresponding to our solve(a,b) seed data for MVP
        mock_test_cases = [
            {"inputs": [2, 3], "expected": 5},
            {"inputs": [-1, 1], "expected": 0},
            {"inputs": [10, 20], "expected": 30}
        ]
        
        run_results = run_student_code(user_answer, mock_test_cases)
        
        if run_results["passed"] == len(mock_test_cases):
            is_correct = True
        else:
            is_correct = False
            
        passed_tests = run_results["passed"]
        
        # Override the original explanation mapping to show actual run traces
        explanation = run_results["output_log"]

    feedback = "Correct" if is_correct else "Incorrect"
    
    return {
        "status": feedback,
        "is_correct": is_correct,
        "explanation": explanation if explanation else "Please review the material and try again.",
        "passed_test_count": passed_tests
    }
