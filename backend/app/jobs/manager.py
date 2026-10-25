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
_cancel_flags: dict[str, threading.Event] = {}
_processes: dict[str, object] = {}
_state_lock = threading.Lock()


def request_cancel(session_id: str) -> None:
    with _state_lock:
        event = _cancel_flags.setdefault(session_id, threading.Event())
        event.set()
        process = _processes.get(session_id)
    if process is not None:
        terminate_process(process)


def is_cancelled(session_id: str) -> bool:
    event = _cancel_flags.get(session_id)
    return event.is_set() if event else False


def register_process(session_id: str, process: object) -> None:
    with _state_lock:
        _processes[session_id] = process
    if is_cancelled(session_id):
        terminate_process(process)


def unregister_process(session_id: str, process: object) -> None:
    with _state_lock:
        if _processes.get(session_id) is process:
            _processes.pop(session_id, None)


def terminate_process(process: object) -> None:
    terminate = getattr(process, "terminate", None)
    if callable(terminate):
        terminate()
    poll = getattr(process, "poll", None)
    kill = getattr(process, "kill", None)
    if callable(poll) and callable(kill) and poll() is None:
        kill()


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
        _cancel_flags.setdefault(session_id, threading.Event())
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
                acquired = True

            row.status = JobStatus.validating
            row.started_at = datetime.now(timezone.utc)
            db.commit()

            start = time.monotonic()
            result_holder: dict = {}
            error_holder: dict = {}

            def _target():
                worker_db = SessionLocal()
                try:
                    worker_row = worker_db.get(SessionModel, session_id)
                    if worker_row is None or is_cancelled(session_id):
                        return
                    worker_row.status = JobStatus.running
                    worker_db.commit()
                    result_holder["ok"] = True
                    work_fn(worker_db, worker_row, lambda: is_cancelled(session_id))
                except Exception as exc:  # noqa: BLE001
                    error_holder["error"] = str(exc)
                finally:
                    worker_db.close()

            t = threading.Thread(target=_target, daemon=True)
            t.start()
            t.join(timeout=settings.job_timeout_seconds)

            elapsed = time.monotonic() - start
            row.duration_seconds = elapsed
            row.finished_at = datetime.now(timezone.utc)

            if t.is_alive():
                with _state_lock:
                    process = _processes.get(session_id)
                if process is not None:
                    terminate_process(process)
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
            with _state_lock:
                _cancel_flags.pop(session_id, None)
                _processes.pop(session_id, None)
            if acquired:
                _lock.release()
            db.close()

    threading.Thread(target=_runner, daemon=True).start()
