from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask import has_request_context, request, session

from app.models import AuditLog, User, db


def _request_ip() -> Optional[str]:
    if not has_request_context():
        return None
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def _resolve_actor_id(explicit_user_id: Optional[int]) -> Optional[int]:
    if explicit_user_id is not None:
        return explicit_user_id
    if has_request_context():
        return session.get("user_id")
    return None


def log_action(
    action: str,
    *,
    user_id: Optional[int] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    commit: bool = False,
) -> AuditLog:
    entry = AuditLog(
        user_id=_resolve_actor_id(user_id),
        action=action,
        target_type=target_type,
        target_id=target_id,
        details_json=json.dumps(details, ensure_ascii=False) if details else None,
        ip_address=ip_address or _request_ip(),
    )
    db.session.add(entry)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return entry


def list_audit_logs(
    *,
    page: int = 1,
    per_page: int = 25,
    search: str = "",
    action_filter: str = "",
    user_filter: str = "",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    query = AuditLog.query.order_by(AuditLog.created_at.desc())

    if action_filter:
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))

    if user_filter:
        like = f"%{user_filter.strip()}%"
        query = (
            query.outerjoin(User, AuditLog.user_id == User.id)
            .filter(
                db.or_(
                    User.full_name.ilike(like),
                    User.email.ilike(like),
                    User.username.ilike(like),
                )
            )
        )

    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            db.or_(
                AuditLog.action.ilike(like),
                AuditLog.target_type.ilike(like),
                AuditLog.details_json.ilike(like),
            )
        )

    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(AuditLog.created_at >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(AuditLog.created_at < end)
        except ValueError:
            pass

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


def recent_actions(limit: int = 5) -> List[AuditLog]:
    return (
        AuditLog.query.order_by(AuditLog.created_at.desc())
        .limit(max(1, int(limit)))
        .all()
    )
