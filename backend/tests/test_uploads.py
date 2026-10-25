import io


def test_reject_bad_extension(client):
    resp = client.post(
        "/api/uploads/capture",
        files={"file": ("evil.exe", io.BytesIO(b"not a capture"), "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_accept_pcap_extension(client):
    resp = client.post(
        "/api/uploads/capture",
        files={"file": ("test.pcap", io.BytesIO(b"\xd4\xc3\xb2\xa1" + b"\x00" * 20), "application/octet-stream")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "upload_id" in body
    assert body["size_bytes"] == 24


def test_upload_size_limit(client, monkeypatch):
    from app.core import config
    monkeypatch.setattr(config.settings, "max_upload_mb", 0)  # 0 MB -> anything triggers limit
    resp = client.post(
        "/api/uploads/capture",
        files={"file": ("big.pcap", io.BytesIO(b"x" * 2048), "application/octet-stream")},
    )
    assert resp.status_code == 413


def test_path_traversal_rejected():
    from fastapi import HTTPException
    from app.core.security import safe_join
    import pytest as _pytest
    with _pytest.raises(HTTPException):
        safe_join("/tmp/somewhere", "../../etc/passwd")
