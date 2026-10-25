from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from app.adapters import awareness as awareness_adapter
from app.adapters import metasploit as msf_adapter
from app.adapters import wireless as wireless_adapter
from app.adapters.registry import get_scenario
from app.core.config import settings
from app.core.database import get_db
from app.core.security import safe_join, verify_access
from app.jobs.manager import is_cancelled, request_cancel, run_job
from app.models.awareness import AwarenessAttempt
from app.models.finding import Finding
from app.models.session import (
    ExecutionMode,
    JobStatus,
    ModuleType,
    SecurityOutcome,
    Session as SessionModel,
)
from app.schemas.session import (
    SessionCreateAwareness,
    SessionCreateMetasploit,
    SessionCreateWireless,
    SessionListItem,
    SessionOut,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"], dependencies=[Depends(verify_access)])


def _current_mode() -> ExecutionMode:
    return ExecutionMode.real if settings.execution_mode == "real" else ExecutionMode.demonstration


def _add_finding(db: DBSession, session: SessionModel, title: str, severity: str, summary: str) -> None:
    db.add(Finding(session_id=session.id, module=session.module.value, title=title, severity=severity, summary=summary))


# ---------------------------------------------------------------- Wireless
@router.post("/wireless", response_model=SessionOut)
def create_wireless_session(payload: SessionCreateWireless, db: DBSession = Depends(get_db)):
    scenario = get_scenario(payload.scenario_id)
    if not scenario or scenario.module not in ("wireless_wep", "wireless_wpa"):
        raise HTTPException(404, "Unknown wireless scenario")

    capture_path = _find_upload(payload.capture_upload_id)
    if not capture_path:
        raise HTTPException(404, "Uploaded capture not found; please re-upload")

    wordlist_path: Optional[Path] = None
    if scenario.requires_wordlist:
        if not payload.wordlist_id:
            raise HTTPException(400, "This scenario requires selecting a wordlist")
        wordlist_path = safe_join(settings.wordlist_dir, payload.wordlist_id)
        if not wordlist_path.exists():
            raise HTTPException(404, "Wordlist not found")

    session = SessionModel(
        name=payload.name,
        module=ModuleType(scenario.module),
        scenario_id=scenario.id,
        status=JobStatus.queued,
        execution_mode=_current_mode(),
        input_summary={"capture_upload_id": payload.capture_upload_id, "wordlist_id": payload.wordlist_id},
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    demo = _current_mode() == ExecutionMode.demonstration

    def work(db2: DBSession, row: SessionModel, check_cancelled):
        if scenario.id == "wep_key_recovery_demo":
            result = wireless_adapter.run_wep_recovery(capture_path, demonstration=demo)
        else:
            result = wireless_adapter.run_wpa_dictionary_test(capture_path, wordlist_path, demonstration=demo)
        row.outcome = SecurityOutcome(result.outcome)
        row.evidence = result.evidence
        row.explanation = result.explanation
        row.raw_log = result.raw_log
        row.fixture_provenance = "demonstration-fixture" if demo else "uploaded-capture"
        if result.outcome == "key_recovered":
            _add_finding(db2, row, f"{scenario.title}: key recovered", "finding", "A key was recovered from the provided capture. See session detail for evidence.")
        elif result.outcome == "not_found_in_wordlist":
            _add_finding(db2, row, f"{scenario.title}: not found in wordlist", "info", "Passphrase was not present in the tested wordlist. This does not mean the network is secure.")
        else:
            _add_finding(db2, row, f"{scenario.title}: evidence invalid", "warning", row.raw_log[:200])
        db2.commit()

    run_job(session.id, work)
    db.refresh(session)
    return session


# ------------------------------------------------------------- Metasploit
@router.post("/metasploit", response_model=SessionOut)
def create_metasploit_session(payload: SessionCreateMetasploit, db: DBSession = Depends(get_db)):
    scenario = get_scenario(payload.scenario_id)
    if not scenario or scenario.module != "metasploit":
        raise HTTPException(404, "Unknown Metasploit scenario")

    session = SessionModel(
        name=payload.name,
        module=ModuleType.metasploit,
        scenario_id=scenario.id,
        status=JobStatus.queued,
        execution_mode=_current_mode(),
        input_summary={"target_host": settings.lab_target_host or "not configured"},
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    demo = _current_mode() == ExecutionMode.demonstration

    def work(db2: DBSession, row: SessionModel, check_cancelled):
        result = msf_adapter.run_vsftpd_backdoor_scenario(demonstration=demo)
        row.outcome = SecurityOutcome(result.outcome)
        row.evidence = result.evidence
        row.explanation = result.explanation
        row.raw_log = result.raw_log
        row.fixture_provenance = "demonstration-fixture" if demo else f"live-target:{settings.lab_target_host}"
        if result.outcome == "exploit_confirmed":
            _add_finding(db2, row, f"{scenario.title}: confirmed", "finding", "The backdoor was confirmed against the configured lab target.")
        elif result.outcome == "exploit_not_confirmed":
            _add_finding(db2, row, f"{scenario.title}: not confirmed", "info", "Exploit attempt ran but success was not confirmed.")
        else:
            _add_finding(db2, row, f"{scenario.title}: invalid", "warning", row.raw_log[:200])
        db2.commit()

    run_job(session.id, work)
    db.refresh(session)
    return session


# -------------------------------------------------------------- Awareness
@router.get("/awareness/scenarios")
def list_awareness_scenarios():
    return [
        {"id": s.id, "title": s.title, "brand": s.brand, "narrative": s.narrative,
         "steps": [{"id": st.id, "prompt": st.prompt, "options": st.options} for st in s.steps]}
        for s in awareness_adapter.SCENARIOS.values()
    ]


@router.get("/awareness/dummy-credentials")
def get_dummy_credentials():
    return awareness_adapter.DUMMY_CREDENTIALS


@router.post("/awareness", response_model=SessionOut)
def create_awareness_session(payload: SessionCreateAwareness, db: DBSession = Depends(get_db)):
    scenario = awareness_adapter.SCENARIOS.get(payload.scenario_id)
    if not scenario:
        raise HTTPException(404, "Unknown awareness scenario")

    session = SessionModel(
        name=payload.name,
        module=ModuleType.awareness,
        scenario_id=scenario.id,
        status=JobStatus.succeeded,  # awareness has no background job; created fully formed below
        outcome=SecurityOutcome.not_applicable,
        execution_mode=ExecutionMode.real,  # the simulation itself always genuinely runs
        input_summary={},
        evidence={},
        explanation={
            "objective": "Help students recognize social-engineering cues in a fictional captive portal.",
            "proves": "Nothing about real networks -- this is an original, invented scenario, not a real brand.",
            "does_not_prove": "N/A",
            "defense": "Treat urgency, oversharing requests, and inconsistent branding on any captive portal as red flags.",
        },
        fixture_provenance="fictional-simulation",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/awareness/{session_id}/submit", response_model=SessionOut)
def submit_awareness_decisions(session_id: str, decisions: dict[str, str], db: DBSession = Depends(get_db)):
    session = db.get(SessionModel, session_id)
    if not session or session.module != ModuleType.awareness:
        raise HTTPException(404, "Session not found")

    spotted, total, score = awareness_adapter.score_attempt(session.scenario_id, decisions)
    deb = awareness_adapter.debrief(session.scenario_id, decisions)

    attempt = AwarenessAttempt(
        session_id=session.id, scenario_id=session.scenario_id, decisions=decisions,
        red_flags_spotted=spotted, red_flags_total=total, score=score,
    )
    db.add(attempt)

    session.outcome = SecurityOutcome.awareness_scored
    session.evidence = {"decisions": decisions, "debrief": deb}
    session.input_summary = {"score": score, "red_flags_spotted": spotted, "red_flags_total": total}
    _add_finding(db, session, f"Awareness: {session.scenario_id}", "info", f"Scored {score}/100 ({spotted}/{total} red flags spotted).")
    db.commit()
    db.refresh(session)
    return session


# ---------------------------------------------------------------- Generic
@router.get("", response_model=list[SessionListItem])
def list_sessions(module: Optional[str] = None, status_filter: Optional[str] = Query(None, alias="status"), db: DBSession = Depends(get_db)):
    q = db.query(SessionModel)
    if module:
        q = q.filter(SessionModel.module == module)
    if status_filter:
        q = q.filter(SessionModel.status == status_filter)
    return q.order_by(SessionModel.created_at.desc()).all()


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@router.post("/{session_id}/cancel", response_model=SessionOut)
def cancel_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    request_cancel(session_id)
    return session


@router.delete("/{session_id}")
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    db.query(Finding).filter(Finding.session_id == session_id).delete()
    db.query(AwarenessAttempt).filter(AwarenessAttempt.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"deleted": True}


def _find_upload(upload_id: str) -> Optional[Path]:
    up_dir = Path(settings.upload_dir)
    matches = list(up_dir.glob(f"{upload_id}.*"))
    return matches[0] if matches else None
