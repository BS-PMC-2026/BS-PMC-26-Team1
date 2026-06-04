from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.models import Module, ModuleProgress, ProgressRecord, User
from app.services.progress_service import build_progress_stats
from app.services.settings_service import get_setting_int


@dataclass
class CertificateEligibility:
    eligible: bool
    user: User
    score: int
    modules_completed: int
    modules_total: int
    min_required_score: int
    missing_modules: List[str]
    issued_on: str


def evaluate_certificate(user: User) -> CertificateEligibility:
    record = ProgressRecord.query.filter_by(user_id=user.id).first()
    stats = build_progress_stats(record, user.id)
    min_score = get_setting_int("min_completion_score", 70)

    progress_rows = {
        row.module_id: row
        for row in ModuleProgress.query.filter_by(user_id=user.id).all()
    }
    modules = Module.query.order_by(Module.display_order.asc()).all()
    missing: List[str] = []
    for module in modules:
        row = progress_rows.get(module.id)
        if not row or not row.completed:
            missing.append(module.name)

    # Use the unique-questions-correct ratio as the certificate score —
    # it is a fairer signal than the cumulative attempt success rate, which
    # punishes students for legitimate retries.
    if stats.exercises_total:
        certificate_score = int(round((stats.exercises_correct / stats.exercises_total) * 100))
    else:
        certificate_score = int(stats.success_rate)

    eligible = (
        stats.modules_total > 0
        and stats.modules_completed == stats.modules_total
        and certificate_score >= min_score
        and not missing
    )

    return CertificateEligibility(
        eligible=eligible,
        user=user,
        score=certificate_score,
        modules_completed=stats.modules_completed,
        modules_total=stats.modules_total,
        min_required_score=min_score,
        missing_modules=missing,
        issued_on=datetime.utcnow().strftime("%Y-%m-%d"),
    )


def build_certificate_pdf(eligibility: CertificateEligibility) -> bytes:
    """
    Generate a minimal valid single-page PDF (printable in any reader).
    Implemented manually to avoid extra third-party dependencies for the defense build.
    """
    full_name = eligibility.user.full_name
    issued_on = eligibility.issued_on
    score_text = f"Score: {eligibility.score}% (minimum {eligibility.min_required_score}% required)"
    modules_text = f"Modules completed: {eligibility.modules_completed}/{eligibility.modules_total}"

    def _escape(s: str) -> str:
        return (
            s.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )

    content_stream = (
        "BT\n"
        "/F1 28 Tf\n"
        "120 700 Td\n"
        f"({_escape('Certificate of Completion')}) Tj\n"
        "0 -50 Td\n"
        "/F1 18 Tf\n"
        f"({_escape('ANTE CI/CD Academy')}) Tj\n"
        "0 -60 Td\n"
        "/F1 16 Tf\n"
        f"({_escape('Awarded to: ' + full_name)}) Tj\n"
        "0 -40 Td\n"
        f"({_escape(modules_text)}) Tj\n"
        "0 -30 Td\n"
        f"({_escape(score_text)}) Tj\n"
        "0 -40 Td\n"
        f"({_escape('Issued on: ' + issued_on)}) Tj\n"
        "0 -60 Td\n"
        "/F1 12 Tf\n"
        f"({_escape('This certificate confirms successful completion of the CI/CD learning path.')}) Tj\n"
        "ET\n"
    )

    objects: List[bytes] = []

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 792 612] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
    )
    stream_bytes = content_stream.encode("latin-1", errors="replace")
    objects.append(
        f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1")
        + stream_bytes
        + b"\nendstream"
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray()
    out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets: List[int] = []
    for idx, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{idx} 0 obj\n".encode("latin-1") + body + b"\nendobj\n"

    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode("latin-1")
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("latin-1")
        + b"startxref\n"
        + f"{xref_pos}\n".encode("latin-1")
        + b"%%EOF\n"
    )
    return bytes(out)


def certificate_filename(user: User) -> str:
    safe_name = "_".join(part for part in (user.full_name or "student").split() if part)
    return f"certificate_{safe_name or 'student'}.pdf"


def progress_summary_for_certificate(user: User) -> Optional[CertificateEligibility]:
    return evaluate_certificate(user)
