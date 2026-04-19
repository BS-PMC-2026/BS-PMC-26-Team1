import csv
from pathlib import Path

from app.models import User


def export_users_live_snapshot() -> None:
    """
    Exports users table to a project-visible CSV file.
    Intended for SQL Server live monitoring in Cursor explorer.
    """
    try:
        project_root = Path(__file__).resolve().parents[2]
        out_dir = project_root / "db_sqlserver_live"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "users.csv"

        users = User.query.order_by(User.id.asc()).all()
        with out_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "id",
                    "username",
                    "full_name",
                    "email",
                    "role",
                    "created_at",
                    "is_active",
                ]
            )
            for u in users:
                writer.writerow(
                    [
                        u.id,
                        u.username,
                        u.full_name,
                        u.email,
                        u.role,
                        u.created_at,
                        u.is_active,
                    ]
                )
    except Exception:
        # Do not block registration flow if export fails.
        pass
