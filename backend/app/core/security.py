"""
Minimal access control and safety helpers.
"""
from __future__ import annotations

import ipaddress
import re
from pathlib import Path

from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_access(authorization: str | None = Header(default=None)) -> None:
    if not settings.require_access_token:
        return
    if not settings.access_token or authorization != "Bearer " + settings.access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid access token")


def is_within_cidr(ip: str, cidr: str) -> bool:
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False


def safe_join(base_dir: str, filename: str) -> Path:
    """Resolve `filename` under `base_dir`, rejecting path traversal."""
    base = Path(base_dir).resolve()
    candidate = (base / filename).resolve()
    if candidate != base and base not in candidate.parents:
        raise HTTPException(status_code=400, detail="Invalid file path")
    return candidate


def redact(text: str) -> str:
    """Redact password-like values from tool output."""
    return re.sub(
        r"(?i)(password|psk|key)\s*[:=]\s*\S+",
        r"\1: [REDACTED-SEE-EVIDENCE-FIELD]",
        text,
    )
