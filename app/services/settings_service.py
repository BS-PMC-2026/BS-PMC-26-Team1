from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from flask import session

from app.models import SystemSetting, db


DEFAULT_SETTINGS: Dict[str, str] = {
    "system_name": "ANTE CI/CD Academy",
    "maintenance_mode": "0",
    "min_password_length": "8",
    "min_completion_score": "70",
}


def get_setting(key: str, default: Optional[str] = None) -> str:
    row = db.session.get(SystemSetting, key)
    if row is not None:
        return row.value
    if default is not None:
        return default
    return DEFAULT_SETTINGS.get(key, "")


def get_setting_int(key: str, default: int) -> int:
    raw = get_setting(key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def get_setting_bool(key: str, default: bool = False) -> bool:
    raw = get_setting(key)
    if raw is None or raw == "":
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def set_setting(key: str, value: str, *, updated_by: Optional[int] = None) -> SystemSetting:
    row = db.session.get(SystemSetting, key)
    if row is None:
        row = SystemSetting(key=key, value=str(value), updated_by=updated_by)
        db.session.add(row)
    else:
        row.value = str(value)
        row.updated_by = updated_by
        row.updated_at = datetime.utcnow()
    return row


def all_settings() -> Dict[str, str]:
    rows = SystemSetting.query.all()
    out: Dict[str, str] = dict(DEFAULT_SETTINGS)
    for r in rows:
        out[r.key] = r.value
    return out


def ensure_defaults() -> None:
    for key, value in DEFAULT_SETTINGS.items():
        if db.session.get(SystemSetting, key) is None:
            db.session.add(SystemSetting(key=key, value=value))
    db.session.commit()


def is_maintenance_mode() -> bool:
    return get_setting_bool("maintenance_mode", False)


def current_user_id() -> Optional[int]:
    try:
        return session.get("user_id")
    except RuntimeError:
        return None
