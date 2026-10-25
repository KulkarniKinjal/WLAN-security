"""
In-process job manager.

Documented limitation (per spec section 7): this runs as a single
application worker using Python threads. It is adequate for a single
student running one lab on one laptop; it is NOT a distributed job
queue and will not survive multiple backend processes sharing one DB
safely. Concurrency is capped by settings.max_concurrent_jobs.

On backend restart, any session left in 'running'/'validating' is
marked 'failed' with an explanatory error (see recover_interrupted_jobs)
since the actual child process is gone -- we never claim an
unverifiable job silently "succeeded".
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.session import JobStatus, Session as SessionModel

_lock = threading.Semaphore(settings.max_concurrent_jobs)
_cancel_flags: dict[str, bool] = {}


def request_cancel(session_id: str) -> None:
    _cancel_flags[session_id] = True


def is_cancelled(session_id: str) -> bool:
    return _cancel_flags.get(session_id, False)


def recover_interrupted_jobs() -> None:
    db: DBSession = SessionLocal()
    try:
        stuck = db.query(SessionModel).filter(
            SessionModel.status.in_([JobStatus.queued, JobStatus.validating, JobStatus.running])
        ).all()
        for s in stuck:
            s.status = JobStatus.failed
            s.error_message = "Backend restarted while this job was in progress; it could not be verified and was marked failed. Please re-run."
            s.finished_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


def run_job(session_id: str, work_fn) -> None:
    """Runs `work_fn(db, session_row, check_cancelled)` in a background
    thread, bounded by a timeout and the global concurrency semaphore.
    `work_fn` must update session_row.outcome/evidence/explanation/raw_log
    and return nothing; this wrapper manages status transitions."""

    def _runner():
        acquired = _lock.acquire(timeout=1)
        db: DBSession = SessionLocal()
        try:
            row = db.get(SessionModel, session_id)
            if row is None:
                return
            if not acquired:
                row.status = JobStatus.queued
                db.commit()
                # Simple retry loop respecting max_concurrent_jobs
                while not _lock.acquire(timeout=2):
                    if is_cancelled(session_id):
                        row.status = JobStatus.cancelled
                        row.finished_at = datetime.now(timezone.utc)
                        db.commit()
                        return

            row.status = JobStatus.validating
            row.started_at = datetime.now(timezone.utc)
            db.commit()

            start = time.monotonic()
            result_holder: dict = {}
            error_holder: dict = {}

            def _target():
                try:
                    row.status = JobStatus.running
                    db.commit()
                    result_holder["ok"] = True
                    work_fn(db, row, lambda: is_cancelled(session_id))
                except Exception as exc:  # noqa: BLE001
                    error_holder["error"] = str(exc)

            t = threading.Thread(target=_target, daemon=True)
            t.start()
            t.join(timeout=settings.job_timeout_seconds)

            elapsed = time.monotonic() - start
            row.duration_seconds = elapsed
            row.finished_at = datetime.now(timezone.utc)

            if t.is_alive():
                row.status = JobStatus.timed_out
                row.error_message = f"Job exceeded the {settings.job_timeout_seconds}s timeout."
            elif is_cancelled(session_id):
                row.status = JobStatus.cancelled
            elif "error" in error_holder:
                row.status = JobStatus.failed
                row.error_message = error_holder["error"][:500]
            else:
                row.status = JobStatus.succeeded
            db.commit()
        finally:
            _cancel_flags.pop(session_id, None)
            if acquired:
                _lock.release()
            db.close()

    threading.Thread(target=_runner, daemon=True).start()
