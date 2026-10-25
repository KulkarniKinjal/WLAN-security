from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.database import get_db
from app.core.doctor import run_all_checks
from app.core.security import verify_access
from app.models.finding import Finding
from app.models.session import JobStatus, Session as SessionModel

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(verify_access)])


@router.get("")
def get_dashboard(db: DBSession = Depends(get_db)):
    checks = run_all_checks()
    overall = "passed"
    if any(c.status == "failed" for c in checks):
        overall = "failed"
    elif any(c.status in {"warning", "manual"} for c in checks):
        overall = "warning"

    status_counts = dict(
        db.query(SessionModel.status, func.count(SessionModel.id)).group_by(SessionModel.status).all()
    )
    status_counts = {k.value if hasattr(k, "value") else k: v for k, v in status_counts.items()}

    recent = (
        db.query(SessionModel)
        .order_by(SessionModel.created_at.desc())
        .limit(10)
        .all()
    )

    findings = (
        db.query(Finding)
        .order_by(Finding.created_at.desc())
        .limit(20)
        .all()
    )
    findings_by_module: dict[str, list[dict]] = {}
    for f in findings:
        findings_by_module.setdefault(f.module, []).append({
            "id": f.id, "title": f.title, "severity": f.severity, "summary": f.summary, "created_at": f.created_at.isoformat(),
        })

    return {
        "environment_readiness": overall,
        "execution_mode": settings.execution_mode,
        "status_counts": {
            "queued": status_counts.get("queued", 0),
            "validating": status_counts.get("validating", 0),
            "running": status_counts.get("running", 0),
            "succeeded": status_counts.get("succeeded", 0),
            "failed": status_counts.get("failed", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "timed_out": status_counts.get("timed_out", 0),
        },
        "recent_sessions": [
            {
                "id": s.id, "name": s.name, "module": s.module.value, "status": s.status.value,
                "outcome": s.outcome.value, "execution_mode": s.execution_mode.value,
                "created_at": s.created_at.isoformat(),
            } for s in recent
        ],
        "findings_by_module": findings_by_module,
    }
