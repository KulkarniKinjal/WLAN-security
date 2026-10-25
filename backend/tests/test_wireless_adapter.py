from pathlib import Path

from app.adapters import wireless


def test_wep_demo_mode_labeled_fixture():
    result = wireless.run_wep_recovery(Path("/nonexistent.pcap"), demonstration=True)
    assert result.evidence["fixture"] is True
    assert result.outcome == "key_recovered"


def test_wep_real_mode_missing_tool_reports_honestly(monkeypatch):
    monkeypatch.setattr(wireless, "tool_available", lambda p: False)
    result = wireless.run_wep_recovery(Path("/nonexistent.pcap"), demonstration=False)
    assert result.outcome == "evidence_invalid"
    assert "not found" in result.raw_log.lower()


def test_wpa_real_mode_without_handshake_rejected(monkeypatch, tmp_path):
    capture = tmp_path / "no_handshake.pcap"
    capture.write_bytes(b"not a real capture")
    monkeypatch.setattr(wireless, "_has_complete_eapol_handshake", lambda p: (False, "0 EAPOL frames found"))
    result = wireless.run_wpa_dictionary_test(capture, tmp_path / "wordlist.txt", demonstration=False)
    assert result.outcome == "evidence_invalid"
    assert "handshake" in result.raw_log.lower()


def test_wpa_handshake_requires_messages_from_one_exchange(monkeypatch, tmp_path):
    capture = tmp_path / "handshake.pcap"
    capture.write_bytes(b"capture")

    monkeypatch.setattr(wireless, "tool_available", lambda p: True)
    def fake_run(args, **kwargs):
        result = type("Result", (), {})()
        result.stdout = "" if any("auth_alg" in arg for arg in args) else "aa:bb:cc:dd:ee:ff\t11:22:33:44:55:66\taa:bb:cc:dd:ee:ff\t1\n"
        result.stderr = ""
        return result

    monkeypatch.setattr(
        wireless.subprocess,
        "run",
        fake_run,
    )
    valid, detail = wireless._has_complete_eapol_handshake(capture)
    assert valid is False
    assert "complete 4-way" in detail


def test_wpa_handshake_accepts_message_numbers_for_one_client(monkeypatch, tmp_path):
    capture = tmp_path / "handshake.pcap"
    capture.write_bytes(b"capture")

    class Completed:
        def __init__(self, stdout):
            self.stdout = stdout
            self.stderr = ""

    lines = "\n".join(
        f"aa:bb:cc:dd:ee:ff\t11:22:33:44:55:66\taa:bb:cc:dd:ee:ff\t{i}"
        for i in (1, 2, 3, 4)
    )
    monkeypatch.setattr(wireless, "tool_available", lambda p: True)
    monkeypatch.setattr(
        wireless.subprocess,
        "run",
        lambda args, **kwargs: Completed("" if any("auth_alg" in arg for arg in args) else lines),
    )
    valid, detail = wireless._has_complete_eapol_handshake(capture)
    assert valid is True
    assert "Complete 4-way handshake" in detail


def test_wpa_demo_mode_reports_not_found_not_secure():
    result = wireless.run_wpa_dictionary_test(Path("/a"), Path("/b"), demonstration=True)
    assert result.outcome == "not_found_in_wordlist"
    assert "does not mean" in result.explanation["does_not_prove"].lower() or "not found" in result.outcome
