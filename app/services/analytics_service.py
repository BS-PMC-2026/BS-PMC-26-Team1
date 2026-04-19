from statistics import mean

from app.models import AnalyticsRecord, ExerciseAttempt, Module, Question, User, db


def refresh_user_analytics(user_id: int) -> None:
    modules = Module.query.order_by(Module.display_order.asc()).all()
    for module in modules:
        module_attempts = (
            ExerciseAttempt.query.join(Question, ExerciseAttempt.question_id == Question.id)
            .filter(
                ExerciseAttempt.user_id == user_id,
                Question.module_id == module.id,
            )
            .all()
        )

        attempts_count = len(module_attempts)
        avg_score = float(mean([a.score for a in module_attempts])) if module_attempts else 0.0
        success_rate = (
            float(sum(1 for a in module_attempts if a.is_correct) / attempts_count * 100)
            if attempts_count
            else 0.0
        )

        record = AnalyticsRecord.query.filter_by(user_id=user_id, module_id=module.id).first()
        if not record:
            record = AnalyticsRecord(user_id=user_id, module_id=module.id)
            db.session.add(record)

        record.avg_score = round(avg_score, 2)
        record.attempts_count = attempts_count
        record.success_rate = round(success_rate, 2)


def get_lecturer_dashboard_metrics():
    students = User.query.filter_by(role="student").order_by(User.full_name.asc()).all()
    modules = Module.query.order_by(Module.display_order.asc()).all()
    analytics_rows = AnalyticsRecord.query.all()

    by_student = {student.id: [] for student in students}
    for row in analytics_rows:
        by_student.setdefault(row.user_id, []).append(row)

    student_performance = []
    for student in students:
        rows = by_student.get(student.id, [])
        avg_success = round(mean([r.success_rate for r in rows]), 2) if rows else 0.0
        total_attempts = sum(r.attempts_count for r in rows)
        student_performance.append(
            {
                "student": student,
                "avg_success_rate": avg_success,
                "total_attempts": total_attempts,
            }
        )

    module_weakness = []
    for module in modules:
        module_rows = [r for r in analytics_rows if r.module_id == module.id and r.attempts_count > 0]
        module_success_avg = round(mean([r.success_rate for r in module_rows]), 2) if module_rows else 0.0
        module_weakness.append(
            {
                "module": module,
                "avg_success_rate": module_success_avg,
            }
        )

    module_weakness.sort(key=lambda x: x["avg_success_rate"])
    overall_average = round(mean([m["avg_success_rate"] for m in module_weakness]), 2) if module_weakness else 0.0

    return {
        "students_count": len(students),
        "overall_average_success": overall_average,
        "student_performance": student_performance,
        "module_weakness": module_weakness,
    }
