from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard, doctor, registry, reports, sessions, uploads
from app.core.config import settings
from app.core.database import init_db
from app.jobs.manager import recover_interrupted_jobs

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    recover_interrupted_jobs()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name, "execution_mode": settings.execution_mode}


app.include_router(dashboard.router)
app.include_router(doctor.router)
app.include_router(registry.router)
app.include_router(sessions.router)
app.include_router(uploads.router)
app.include_router(reports.router)
