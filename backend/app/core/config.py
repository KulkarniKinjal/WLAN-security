"""
Central configuration for WLAN AttackLab backend.

All values are read from environment variables (via a `.env` file in
`backend/`) so that nothing dangerous is hardcoded. See `.env.example`
for the full list with explanations.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_DIR / ".env"), extra="ignore")

    # ---- General -----------------------------------------------------
    app_name: str = "WLAN AttackLab"
    execution_mode: str = "demonstration"  # "real" or "demonstration"
    database_url: str = f"sqlite:///{BACKEND_DIR / 'data' / 'attacklab.db'}"

    # ---- Networking / access control ----------------------------------
    bind_host: str = "127.0.0.1"
    bind_port: int = 8000
    cors_allow_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    require_access_token: bool = False
    access_token: str = ""  # required if require_access_token=True and not bound to loopback

    # ---- Uploads / limits ----------------------------------------------
    upload_dir: str = str(BACKEND_DIR / "data" / "uploads")
    max_upload_mb: int = 50
    max_concurrent_jobs: int = 2
    job_timeout_seconds: int = 180

    # ---- Wireless module ------------------------------------------------
    wordlist_dir: str = str(BACKEND_DIR / "fixtures" / "wordlists")
    capture_fixture_dir: str = str(BACKEND_DIR / "fixtures" / "captures")
    aircrack_ng_path: str = "aircrack-ng"
    tshark_path: str = "tshark"
    capinfos_path: str = "capinfos"

    # ---- Metasploit module -----------------------------------------------
    msfconsole_path: str = "msfconsole"
    lab_target_host: str = ""          # e.g. 192.168.56.20 (host-only network only)
    lab_target_allowed_cidr: str = "192.168.56.0/24"
    lab_target_service_port: int = 21  # example: vsftpd 2.3.4 backdoor on Metasploitable2

    # ---- Reports ---------------------------------------------------------
    reports_dir: str = str(BACKEND_DIR / "data" / "reports")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


settings = Settings()

for d in (
    Path(settings.upload_dir),
    Path(settings.reports_dir),
    Path(settings.database_url.replace("sqlite:///", "")).parent,
):
    d.mkdir(parents=True, exist_ok=True)
