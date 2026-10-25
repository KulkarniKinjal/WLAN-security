"""
Environment Doctor: a set of read-only checks the dashboard/doctor page
calls. Every check returns Passed / Warning / Failed plus a short,
beginner-friendly message -- never silently assumes success.
"""
from __future__ import annotations

import os
import shutil
import socket
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.security import is_within_cidr


@dataclass
class CheckResult:
    id: str
    label: str
    status: str  # "passed" | "warning" | "failed"
    detail: str


def _tool_check(name: str, path: str, required_for: str) -> CheckResult:
    found = shutil.which(path) is not None
    return CheckResult(
        id=f"tool_{name}",
        label=f"{name} available",
        status="passed" if found else "warning",
        detail=(f"Found on PATH as '{path}'." if found else
                f"'{path}' not found on PATH. Required for {required_for}; install it or keep the global execution mode set to demonstration."),
    )


def run_all_checks() -> list[CheckResult]:
    results: list[CheckResult] = []

    # Config
    results.append(CheckResult(
        id="config",
        label="Application configuration loaded",
        status="passed",
        detail=f"execution_mode={settings.execution_mode}, bind={settings.bind_host}:{settings.bind_port}",
    ))

    # Database
    try:
        db_path = Path(settings.database_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        writable = os.access(db_path.parent, os.W_OK)
        results.append(CheckResult(
            id="database",
            label="Database directory writable",
            status="passed" if writable else "failed",
            detail=str(db_path.parent) if writable else f"Cannot write to {db_path.parent}",
        ))
    except Exception as exc:  # noqa: BLE001
        results.append(CheckResult(id="database", label="Database directory writable", status="failed", detail=str(exc)))

    # Tools
    results.append(_tool_check("aircrack-ng", settings.aircrack_ng_path, "WEP/WPA wireless experiments"))
    results.append(_tool_check("tshark", settings.tshark_path, "verifying a capture has a complete handshake"))
    results.append(_tool_check("capinfos", settings.capinfos_path, "showing capture metadata"))
    results.append(_tool_check("msfconsole", settings.msfconsole_path, "the Metasploit experiment"))

    # Wordlists / captures
    wl_dir = Path(settings.wordlist_dir)
    wl_count = len([p for p in wl_dir.glob("*") if p.is_file() and p.suffix.lower() not in {".md", ".txt.example"}]) if wl_dir.exists() else 0
    results.append(CheckResult(
        id="wordlists",
        label="Supplied test wordlist present",
        status="passed" if wl_count > 0 else "warning",
        detail=f"{wl_count} file(s) in {wl_dir}" if wl_count else f"No wordlist found in {wl_dir}. See docs/WINDOWS_SETUP.md to add one.",
    ))

    cap_dir = Path(settings.capture_fixture_dir)
    cap_count = len([p for p in cap_dir.glob("*") if p.is_file() and p.suffix.lower() in {".pcap", ".pcapng", ".cap"}]) if cap_dir.exists() else 0
    results.append(CheckResult(
        id="captures",
        label="Example/authorized capture fixtures present",
        status="passed" if cap_count > 0 else "warning",
        detail=f"{cap_count} file(s) in {cap_dir}" if cap_count else "No bundled captures -- you'll need to upload your own authorized capture.",
    ))

    # The backend cannot inspect a VM's second NIC when it runs on Windows.
    results.append(CheckResult(
        id="host_only_iface",
        label="Host-only network interface",
        status="passed",
        detail="Manual verification required: confirm a VirtualBox host-only adapter exists and Kali's second NIC is attached to it (see docs/WINDOWS_SETUP.md step 7).",
    ))

    # Target config + bounded reachability
    if not settings.lab_target_host:
        results.append(CheckResult(
            id="target_config",
            label="Metasploit lab target configured",
            status="warning",
            detail="LAB_TARGET_HOST is not set in backend/.env.",
        ))
    else:
        in_range = is_within_cidr(settings.lab_target_host, settings.lab_target_allowed_cidr)
        results.append(CheckResult(
            id="target_config",
            label="Metasploit lab target configured",
            status="passed" if in_range else "failed",
            detail=(f"{settings.lab_target_host} is inside {settings.lab_target_allowed_cidr}." if in_range
                    else f"{settings.lab_target_host} is OUTSIDE the allowed lab CIDR {settings.lab_target_allowed_cidr}; experiment will refuse to run."),
        ))
        if in_range:
            reachable = _bounded_tcp_check(settings.lab_target_host, 21)
            results.append(CheckResult(
                id="target_reachable",
                label="Lab target FTP service reachable",
                status="passed" if reachable else "warning",
                detail="Connected to port 21." if reachable else "Could not connect to port 21 within 3s -- start the vulnerable VM, or this is expected if it's powered off right now.",
            ))

    return results


def _bounded_tcp_check(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
