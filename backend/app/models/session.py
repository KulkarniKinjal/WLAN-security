from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ModuleType(str, enum.Enum):
    wireless_wep = "wireless_wep"
    wireless_wpa = "wireless_wpa"
    metasploit = "metasploit"
    awareness = "awareness"


class JobStatus(str, enum.Enum):
    queued = "queued"
    validating = "validating"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    timed_out = "timed_out"


class SecurityOutcome(str, enum.Enum):
    not_applicable = "not_applicable"
    key_recovered = "key_recovered"
    not_found_in_wordlist = "not_found_in_wordlist"
    exploit_confirmed = "exploit_confirmed"
    exploit_not_confirmed = "exploit_not_confirmed"
    evidence_invalid = "evidence_invalid"
    awareness_scored = "awareness_scored"


class ExecutionMode(str, enum.Enum):
    real = "real"
    demonstration = "demonstration"


class Session(Base):
    """One experiment run (a 'job' + its persisted result)."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    module: Mapped[ModuleType] = mapped_column(Enum(ModuleType))
    scenario_id: Mapped[str] = mapped_column(String(100))
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.queued)
    outcome: Mapped[SecurityOutcome] = mapped_column(Enum(SecurityOutcome), default=SecurityOutcome.not_applicable)
    execution_mode: Mapped[ExecutionMode] = mapped_column(Enum(ExecutionMode))
    fixture_provenance: Mapped[str] = mapped_column(String(300), default="")

    input_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)  # objective/what-proves/what-doesnt/defense
    raw_log: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str] = mapped_column(String(500), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    pid: Mapped[int | None] = mapped_column(nullable=True)  # child process group leader, for cancellation
