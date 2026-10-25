from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.doctor import run_all_checks
from app.core.security import verify_access

router = APIRouter(prefix="/api/doctor", tags=["doctor"], dependencies=[Depends(verify_access)])


@router.get("")
def get_doctor_report():
    checks = run_all_checks()
    overall = "passed"
    if any(c.status == "failed" for c in checks):
        overall = "failed"
    elif any(c.status == "warning" for c in checks):
        overall = "warning"
    return {"overall": overall, "checks": [c.__dict__ for c in checks]}
