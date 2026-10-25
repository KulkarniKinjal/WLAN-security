"""Unit tests for the Metasploit adapter's safety gates, independent of
the API/demo-mode wrapper, so target-validation logic is actually
exercised (this is the real-mode gate)."""
from app.adapters import metasploit as msf
from app.core.config import settings


def test_no_target_configured_blocks(monkeypatch):
    monkeypatch.setattr(settings, "lab_target_host", "")
    ok, msg = msf.validate_target()
    assert ok is False
    assert "No lab target configured" in msg


def test_target_outside_cidr_blocks(monkeypatch):
    monkeypatch.setattr(settings, "lab_target_host", "8.8.8.8")
    monkeypatch.setattr(settings, "lab_target_allowed_cidr", "192.168.56.0/24")
    ok, msg = msf.validate_target()
    assert ok is False
    assert "not inside the allowed lab CIDR" in msg


def test_target_in_cidr_but_unreachable_blocks(monkeypatch):
    monkeypatch.setattr(settings, "lab_target_host", "192.168.56.250")  # unused address in range
    monkeypatch.setattr(settings, "lab_target_allowed_cidr", "192.168.56.0/24")
    ok, msg = msf.validate_target()
    assert ok is False
    assert "not reachable" in msg


def test_demonstration_mode_never_touches_network():
    result = msf.run_vsftpd_backdoor_scenario(demonstration=True)
    assert result.evidence["fixture"] is True
    assert result.outcome == "exploit_confirmed"
    assert "no real exploitation" in result.raw_log.lower() or "fixture" in result.raw_log.lower()
