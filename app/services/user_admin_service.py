from __future__ import annotations

from typing import Dict, Optional

from sqlalchemy import or_

from app.models import (
    AdminProfile,
    AnalyticsRecord,
    AuditLog,
    ExerciseAttempt,
    LecturerProfile,
    LearningState,
    LoginAttempt,
    ModuleProgress,
    PasswordResetToken,
    ProgressRecord,
    StudentProfile,
    User,
    db,
)


def list_users(
    *,
    page: int = 1,
    per_page: int = 20,
    search: str = "",
    role_filter: str = "",
    status_filter: str = "",
) -> Dict:
    query = User.query

    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(like),
                User.email.ilike(like),
                User.username.ilike(like),
            )
        )

    if role_filter in {"student", "lecturer", "admin"}:
        query = query.filter(User.role == role_filter)

    if status_filter == "active":
        query = query.filter(User.is_active.is_(True))
    elif status_filter == "inactive":
        query = query.filter(User.is_active.is_(False))

    query = query.order_by(User.created_at.desc(), User.id.desc())

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


def set_active(user: User, active: bool) -> None:
    user.is_active = bool(active)


def delete_user_cascade(user: User) -> None:
    user_id = user.id
    StudentProfile.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    LecturerProfile.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    AdminProfile.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    ExerciseAttempt.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    ProgressRecord.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    ModuleProgress.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    AnalyticsRecord.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    LearningState.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    PasswordResetToken.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    AuditLog.query.filter_by(user_id=user_id).update({AuditLog.user_id: None}, synchronize_session=False)
    LoginAttempt.query.filter_by(email=(user.email or "").lower()).delete(synchronize_session=False)
    db.session.delete(user)


def count_admins() -> int:
    return User.query.filter_by(role="admin").count()


def find_user(user_id: int) -> Optional[User]:
    return db.session.get(User, user_id)
