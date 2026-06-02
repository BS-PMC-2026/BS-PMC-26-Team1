from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import func

from app.models import ExerciseAttempt, Module, Question, User, db


def _parse_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None


def _date_filtered_attempts(start: Optional[str], end: Optional[str]):
    query = ExerciseAttempt.query
    start_dt = _parse_date(start)
    end_dt = _parse_date(end)
    if start_dt:
        query = query.filter(ExerciseAttempt.submitted_at >= start_dt)
    if end_dt:
        query = query.filter(ExerciseAttempt.submitted_at < end_dt + timedelta(days=1))
    return query


def _csv_bytes(rows: List[List[object]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows:
        writer.writerow(row)
    return "﻿".encode("utf-8") + buf.getvalue().encode("utf-8")


def build_students_report(start: Optional[str], end: Optional[str]) -> Tuple[List[List[object]], bytes]:
    students = User.query.filter_by(role="student").order_by(User.full_name.asc()).all()
    base_attempts = _date_filtered_attempts(start, end)
    rows = [[
        "User ID",
        "Full Name",
        "Email",
        "Joined At",
        "Status",
        "Attempts",
        "Correct",
        "Success Rate (%)",
    ]]
    for student in students:
        student_attempts = base_attempts.filter(ExerciseAttempt.user_id == student.id).all()
        attempts_count = len(student_attempts)
        correct_count = sum(1 for a in student_attempts if a.is_correct)
        success_rate = int((correct_count / attempts_count) * 100) if attempts_count else 0
        rows.append([
            student.id,
            student.full_name,
            student.email,
            student.created_at.strftime("%Y-%m-%d %H:%M") if student.created_at else "",
            "Active" if student.is_active else "Inactive",
            attempts_count,
            correct_count,
            success_rate,
        ])
    return rows, _csv_bytes(rows)


def build_questions_report(start: Optional[str], end: Optional[str]) -> Tuple[List[List[object]], bytes]:
    questions = Question.query.order_by(Question.id.asc()).all()
    base_attempts = _date_filtered_attempts(start, end)
    modules_by_id = {m.id: m for m in Module.query.all()}

    rows = [[
        "Question ID",
        "Module",
        "Type",
        "Difficulty",
        "Active",
        "Attempts",
        "Correct",
        "Success Rate (%)",
    ]]
    for q in questions:
        q_attempts = base_attempts.filter(ExerciseAttempt.question_id == q.id).all()
        attempts_count = len(q_attempts)
        correct_count = sum(1 for a in q_attempts if a.is_correct)
        success_rate = int((correct_count / attempts_count) * 100) if attempts_count else 0
        module_name = modules_by_id.get(q.module_id).name if modules_by_id.get(q.module_id) else "-"
        rows.append([
            q.id,
            module_name,
            q.question_type,
            q.difficulty,
            "Yes" if q.is_active else "No",
            attempts_count,
            correct_count,
            success_rate,
        ])
    return rows, _csv_bytes(rows)


def build_usage_report(start: Optional[str], end: Optional[str]) -> Tuple[List[List[object]], bytes]:
    start_dt = _parse_date(start) or (datetime.utcnow() - timedelta(days=30))
    end_dt = _parse_date(end) or datetime.utcnow()

    rows = [[
        "Date",
        "Attempts",
        "Correct",
        "Unique Students",
        "Success Rate (%)",
    ]]
    day = start_dt
    while day.date() <= end_dt.date():
        next_day = day + timedelta(days=1)
        day_query = ExerciseAttempt.query.filter(
            ExerciseAttempt.submitted_at >= day,
            ExerciseAttempt.submitted_at < next_day,
        )
        attempts_count = day_query.count()
        correct_count = day_query.filter(ExerciseAttempt.is_correct.is_(True)).count()
        unique_students = (
            db.session.query(func.count(func.distinct(ExerciseAttempt.user_id)))
            .filter(
                ExerciseAttempt.submitted_at >= day,
                ExerciseAttempt.submitted_at < next_day,
                ExerciseAttempt.user_id.isnot(None),
            )
            .scalar()
            or 0
        )
        success_rate = int((correct_count / attempts_count) * 100) if attempts_count else 0
        rows.append([
            day.strftime("%Y-%m-%d"),
            attempts_count,
            correct_count,
            unique_students,
            success_rate,
        ])
        day = next_day
    return rows, _csv_bytes(rows)


REPORT_BUILDERS = {
    "students": build_students_report,
    "questions": build_questions_report,
    "usage": build_usage_report,
}

REPORT_LABELS = {
    "students": "Students performance",
    "questions": "Questions difficulty analytics",
    "usage": "Daily platform usage",
}
