from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.session import ExecutionMode, JobStatus, ModuleType, SecurityOutcome


class SessionCreateWireless(BaseModel):
    name: str
    scenario_id: str  # e.g. "wep_key_recovery_demo" or "wpa_dictionary_test"
    capture_upload_id: str
    wordlist_id: Optional[str] = None  # required for WPA scenarios


class SessionCreateMetasploit(BaseModel):
    name: str
    scenario_id: str  # fixed registry id, e.g. "vsftpd_234_backdoor"


class SessionCreateAwareness(BaseModel):
    name: str
    scenario_id: str


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    module: ModuleType
    scenario_id: str
    status: JobStatus
    outcome: SecurityOutcome
    execution_mode: ExecutionMode
    fixture_provenance: str
    input_summary: dict[str, Any]
    evidence: dict[str, Any]
    explanation: dict[str, Any]
    raw_log: str
    error_message: str
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_seconds: Optional[float]


class SessionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    module: ModuleType
    scenario_id: str
    status: JobStatus
    outcome: SecurityOutcome
    execution_mode: ExecutionMode
    created_at: datetime
    duration_seconds: Optional[float]
