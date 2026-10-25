from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.core.reports import generate_json_report, generate_pdf_report
from app.core.security import verify_access
from app.models.session import Session as SessionModel

router = APIRouter(prefix="/api/reports", tags=["reports"], dependencies=[Depends(verify_access)])


@router.get("/{session_id}.pdf")
def get_pdf_report(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    path = generate_pdf_report(session)
    return FileResponse(path, media_type="application/pdf", filename=f"attacklab-{session_id}.pdf")


@router.get("/{session_id}.json")
def get_json_report(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    path = generate_json_report(session)
    return FileResponse(path, media_type="application/json", filename=f"attacklab-{session_id}.json")
