"""Helpers for the lecturer's code-submissions review screen."""

from __future__ import annotations

from typing import Dict, Optional

from sqlalchemy import or_

from app.models import ExerciseAttempt, Question, User, db


def list_code_submissions(
    *,
    page: int = 1,
    per_page: int = 20,
    student_filter: str = "",
    question_filter: Optional[int] = None,
    review_filter: str = "",
) -> Dict:
    query = (
        ExerciseAttempt.query.join(
            Question, ExerciseAttempt.question_id == Question.id
        )
        .filter(Question.question_type == "code")
        .order_by(ExerciseAttempt.submitted_at.desc())
    )

    if student_filter:
        like = f"%{student_filter.strip()}%"
        query = query.join(User, ExerciseAttempt.user_id == User.id).filter(
            or_(
                User.full_name.ilike(like),
                User.email.ilike(like),
                User.username.ilike(like),
            )
        )

    if question_filter:
        query = query.filter(ExerciseAttempt.question_id == int(question_filter))

    if review_filter == "pending":
        query = query.filter(
            or_(ExerciseAttempt.lecturer_review.is_(None), ExerciseAttempt.lecturer_review == "")
        )
    elif review_filter == "reviewed":
        query = query.filter(
            ExerciseAttempt.lecturer_review.isnot(None), ExerciseAttempt.lecturer_review != ""
        )

    per_page = max(1, min(int(per_page), 100))
    page = max(1, int(page))
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    pages = max(1, (total + per_page - 1) // per_page)
    return {
        "rows": rows,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    }


def list_code_questions():
    return (
        Question.query.filter(Question.question_type == "code")
        .order_by(Question.id.asc())
        .all()
    )


def get_submission(attempt_id: int) -> Optional[ExerciseAttempt]:
    return db.session.get(ExerciseAttempt, attempt_id)
