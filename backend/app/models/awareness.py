from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AwarenessAttempt(Base):
    """One run of the captive-portal social-engineering simulator.
    Stores only decisions and a derived score -- never free-text
    credentials, even dummy ones typed by the student."""

    __tablename__ = "awareness_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"))
    scenario_id: Mapped[str] = mapped_column(String(50))
    decisions: Mapped[dict] = mapped_column(JSON, default=dict)  # {step_id: choice}
    red_flags_spotted: Mapped[int] = mapped_column(Integer, default=0)
    red_flags_total: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
