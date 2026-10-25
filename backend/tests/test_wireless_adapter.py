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


def test_wpa_demo_mode_reports_not_found_not_secure():
    result = wireless.run_wpa_dictionary_test(Path("/a"), Path("/b"), demonstration=True)
    assert result.outcome == "not_found_in_wordlist"
    assert "does not mean" in result.explanation["does_not_prove"].lower() or "not found" in result.outcome
