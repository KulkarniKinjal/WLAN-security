"""
Wireless adapter: wraps aircrack-ng (and capinfos/tshark for metadata)
behind a fixed, allowlisted set of operations. No live capture, no
deauthentication, no packet injection anywhere in this module -- it only
ever reads an uploaded file from disk.

Honesty rules enforced here (see project spec section 6.C):
- WEP and WPA use different, explicit code paths.
- A WPA test requires a *complete* EAPOL handshake; we check for that
  with tshark before ever invoking aircrack-ng, and fail with a clear
  message if it's missing or the capture looks like WPA3/SAE.
- "Not found in this wordlist" is reported as exactly that -- never as
  "secure" or "uncrackable".
- We never fabricate a recovered key, handshake, or packet count. If a
  required local tool is missing, we say so and stop (or, in
  demonstration mode, we clearly label the result as a fixture).
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.processes import ProcessResult, run_process
from app.jobs.manager import register_process, unregister_process


@dataclass
class WirelessResult:
    outcome: str  # "key_recovered" | "not_found_in_wordlist" | "evidence_invalid"
    evidence: dict
    explanation: dict
    raw_log: str


def tool_available(path: str) -> bool:
    return shutil.which(path) is not None


def _run_tool(session_id: str, args: list[str], timeout: float, check_cancelled) -> ProcessResult:
    return run_process(
        args, timeout, check_cancelled,
        lambda process: register_process(session_id, process),
        lambda process: unregister_process(session_id, process),
    )


def get_capture_metadata(capture_path: Path) -> dict:
    """Uses capinfos if available; never fabricates values. Returns an
    explicit 'unavailable' marker instead of guessing when the tool is
    missing or the file can't be parsed."""
    if not tool_available(settings.capinfos_path):
        return {"available": False, "reason": "capinfos not installed on this host"}
    try:
        out = subprocess.run(
            [settings.capinfos_path, "-T", "-m", str(capture_path)],
            capture_output=True, text=True, timeout=20,
        )
        if out.returncode != 0:
            return {"available": False, "reason": out.stderr.strip()[:300] or "capinfos failed"}
        return {"available": True, "raw": out.stdout.strip()}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": str(exc)}


def _has_complete_eapol_handshake(capture_path: Path) -> tuple[bool, str]:
    """Checks for a 4-message EAPOL exchange using tshark. Returns
    (has_handshake, detail_message). This does NOT assume any specific
    BSSID; it just checks whether aircrack-ng-usable evidence exists."""
    if not tool_available(settings.tshark_path):
        return False, "tshark not installed; cannot verify handshake completeness before running aircrack-ng"
    try:
        sae = subprocess.run(
            [settings.tshark_path, "-r", str(capture_path), "-Y", "wlan.fixed.auth_alg == 3", "-c", "1"],
            capture_output=True, text=True, timeout=30,
        )
        if sae.stdout.strip():
            return False, "Capture contains WPA3/SAE authentication; WPA/WPA2 dictionary testing does not apply"
        out = subprocess.run(
            [
                settings.tshark_path, "-r", str(capture_path), "-Y",
                "eapol && wlan_rsna_eapol.keydes.msgnr",
                "-T", "fields", "-E", "separator=\t",
                "-e", "wlan.bssid", "-e", "wlan.sa", "-e", "wlan.da",
                "-e", "wlan_rsna_eapol.keydes.msgnr",
            ],
            capture_output=True, text=True, timeout=30,
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"tshark failed to read capture: {exc}"
    exchanges: dict[tuple[str, frozenset[str]], set[str]] = {}
    for line in out.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) != 4:
            continue
        bssid, source, destination, message_number = (field.strip().lower() for field in fields)
        if not bssid or not source or not destination or message_number not in {"1", "2", "3", "4"}:
            continue
        pair = (bssid, frozenset((source, destination)))
        exchanges.setdefault(pair, set()).add(message_number)
    complete = next((pair for pair, messages in exchanges.items() if messages == {"1", "2", "3", "4"}), None)
    if complete is None:
        observed = sorted({message for messages in exchanges.values() for message in messages})
        return False, f"No complete 4-way handshake found for one BSSID/client exchange; observed message numbers: {', '.join(observed) or 'none'}"
    return True, f"Complete 4-way handshake found for BSSID {complete[0]} and its client exchange"


def run_wep_recovery(capture_path: Path, demonstration: bool, session_id: str = "", check_cancelled=lambda: False) -> WirelessResult:
    explanation_base = {
        "objective": "Recover a WEP key from captured IVs using aircrack-ng's statistical attack.",
        "proves": "WEP's key-scheduling algorithm leaks key material once enough unique IVs are captured.",
        "does_not_prove": "Nothing about WPA/WPA2/WPA3 security, and nothing about networks not present in this capture.",
        "defense": "Retire WEP; use WPA2/WPA3 with a strong passphrase or Enterprise auth.",
    }

    if demonstration:
        return WirelessResult(
            outcome="key_recovered",
            evidence={
                "fixture": True,
                "note": "DEMONSTRATION FIXTURE -- no real cracking was performed.",
                "sample_key_ascii": "demo-key-not-real",
            },
            explanation=explanation_base,
            raw_log="[demonstration mode] aircrack-ng was not executed. This is a labeled example of the result UI.",
        )

    if not tool_available(settings.aircrack_ng_path):
        return WirelessResult(
            outcome="evidence_invalid",
            evidence={"fixture": False, "error": "aircrack-ng not found on PATH"},
            explanation=explanation_base,
            raw_log="aircrack-ng is required for this experiment and was not found. Install it inside Kali (see docs/WINDOWS_SETUP.md) and re-run.",
        )

    try:
        result = _run_tool(session_id, [settings.aircrack_ng_path, "-a", "1", str(capture_path)], settings.job_timeout_seconds, check_cancelled)
    except OSError as exc:
        return WirelessResult("evidence_invalid", {"fixture": False, "error": str(exc)}, explanation_base, str(exc))
    if result.interrupted:
        return WirelessResult(
            outcome="evidence_invalid",
            evidence={"fixture": False, "error": result.reason},
            explanation=explanation_base,
            raw_log=f"aircrack-ng did not complete: {result.reason}.",
        )

    log = result.stdout + "\n" + result.stderr
    if result.returncode == 0 and "KEY FOUND" in result.stdout:
        key_line = next((l for l in result.stdout.splitlines() if "KEY FOUND" in l), "")
        return WirelessResult(
            outcome="key_recovered",
            evidence={"fixture": False, "key_line": key_line},
            explanation=explanation_base,
            raw_log=log[-4000:],
        )
    return WirelessResult(
        outcome="evidence_invalid",
        evidence={"fixture": False, "error": f"aircrack-ng exited with code {result.returncode}" if result.returncode else "key_not_found"},
        explanation=explanation_base,
        raw_log=log[-4000:] or "aircrack-ng ran but did not report KEY FOUND. The capture may not contain enough unique IVs.",
    )


def run_wpa_dictionary_test(capture_path: Path, wordlist_path: Path, demonstration: bool, session_id: str = "", check_cancelled=lambda: False) -> WirelessResult:
    explanation_base = {
        "objective": "Test whether the WPA/WPA2-Personal passphrase for the captured handshake appears in a fixed wordlist.",
        "proves": "Whether the specific passphrase is present in the tested wordlist only.",
        "does_not_prove": (
            "A 'not found' result does NOT mean the passphrase is strong or the network is secure -- "
            "it only means this wordlist didn't contain it. This method never applies to WPA3 (SAE)."
        ),
        "defense": "Use a long random passphrase (15+ characters) or move to WPA3-Personal (SAE).",
    }

    if demonstration:
        return WirelessResult(
            outcome="not_found_in_wordlist",
            evidence={"fixture": True, "note": "DEMONSTRATION FIXTURE -- no real dictionary attack was performed.",
                      "wordlist_entries_tried": 14344391},
            explanation=explanation_base,
            raw_log="[demonstration mode] aircrack-ng was not executed.",
        )

    has_handshake, detail = _has_complete_eapol_handshake(capture_path)
    if not has_handshake:
        return WirelessResult(
            outcome="evidence_invalid",
            evidence={"fixture": False, "reason": detail},
            explanation=explanation_base,
            raw_log=f"Pre-check failed: {detail}. A WPA dictionary test requires a complete captured 4-way handshake; this capture does not appear to contain one (or WPA3/SAE was used, which this attack does not apply to).",
        )

    if not tool_available(settings.aircrack_ng_path):
        return WirelessResult(
            outcome="evidence_invalid",
            evidence={"fixture": False, "error": "aircrack-ng not found on PATH"},
            explanation=explanation_base,
            raw_log="aircrack-ng is required and was not found. Install it inside Kali and re-run.",
        )

    try:
        result = _run_tool(session_id, [settings.aircrack_ng_path, "-w", str(wordlist_path), str(capture_path)], settings.job_timeout_seconds, check_cancelled)
    except OSError as exc:
        return WirelessResult("evidence_invalid", {"fixture": False, "error": str(exc)}, explanation_base, str(exc))
    if result.interrupted:
        return WirelessResult(
            outcome="evidence_invalid",
            evidence={"fixture": False, "error": result.reason},
            explanation=explanation_base,
            raw_log=f"aircrack-ng did not complete: {result.reason}. Try a smaller wordlist.",
        )

    log = result.stdout + "\n" + result.stderr
    if result.returncode == 0 and "KEY FOUND" in result.stdout:
        key_line = next((l for l in result.stdout.splitlines() if "KEY FOUND" in l), "")
        return WirelessResult(
            outcome="key_recovered",
            evidence={"fixture": False, "key_line": key_line},
            explanation=explanation_base,
            raw_log=log[-4000:],
        )
    return WirelessResult(
        outcome="not_found_in_wordlist" if result.returncode == 0 else "evidence_invalid",
        evidence={"fixture": False, "error": f"aircrack-ng exited with code {result.returncode}" if result.returncode else "key_not_found"},
        explanation=explanation_base,
        raw_log=log[-4000:] or "aircrack-ng completed; passphrase was not present in the supplied wordlist.",
    )
