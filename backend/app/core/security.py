"""
Minimal access control and safety helpers.

- `verify_access`: simple bearer-token check, only enforced when the
  backend is reachable beyond loopback (see config.require_access_token).
- `is_within_cidr`: used to confirm the configured lab target is inside
  the isolated host-only network before any Metasploit action runs.
- `safe_join`: prevents path traversal when resolving upload/report paths.
"""
from __future__ import annotations

import ipaddress
import os
from pathlib import Path

from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_access(authorization: str | None = Header(default=None)) -> None:
    if not settings.require_access_token:
        return
    expected = f"Bearer {settings.access_token}"
    if not settings.access_token or authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid access token")


def is_within_cidr(ip: str, cidr: str) -> bool:
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False


def safe_join(base_dir: str, filename: str) -> Path:
    """Resolve `filename` under `base_dir`, rejecting any path traversal."""
    base = Path(base_dir).resolve()
    candidate = (base / filename).resolve()
    if not str(candidate).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    return candidate


def redact(text: str) -> str:
    """Very small log redaction helper: strips anything that looks like a
    PSK/password value echoed by a tool so logs shown to students never
    leak more than the single evidence field the UI already discloses."""
    import re

    text = re.sub(r"(?i)(password|psk|key)\s*[:=]\s*\S+", r"\1: [REDACTED-SEE-EVIDENCE-FIELD]", text)
    return text
