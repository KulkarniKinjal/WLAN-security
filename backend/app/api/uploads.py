from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.adapters.wireless import get_capture_metadata
from app.core.config import settings
from app.core.security import safe_join, verify_access

router = APIRouter(prefix="/api/uploads", tags=["uploads"], dependencies=[Depends(verify_access)])

ALLOWED_EXTENSIONS = {".pcap", ".pcapng", ".cap"}


@router.post("/capture")
async def upload_capture(file: UploadFile):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    upload_id = str(uuid.uuid4())
    dest = safe_join(settings.upload_dir, f"{upload_id}{ext}")

    size = 0
    max_bytes = settings.max_upload_mb * 1024 * 1024
    with open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")
            out.write(chunk)

    metadata = get_capture_metadata(dest)
    return {"upload_id": upload_id, "filename": file.filename, "size_bytes": size, "metadata": metadata}


@router.get("/wordlists")
def list_wordlists():
    wl_dir = Path(settings.wordlist_dir)
    if not wl_dir.exists():
        return []
    return [{"id": p.name, "name": p.name, "size_bytes": p.stat().st_size} for p in sorted(wl_dir.glob("*")) if p.is_file()]
