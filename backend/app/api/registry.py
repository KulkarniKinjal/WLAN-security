from __future__ import annotations

from fastapi import APIRouter, Depends

from app.adapters.registry import SCENARIOS
from app.core.security import verify_access

router = APIRouter(prefix="/api/registry", tags=["registry"], dependencies=[Depends(verify_access)])


@router.get("/scenarios")
def list_scenarios():
    return [
        {
            "id": s.id, "module": s.module, "title": s.title, "objective": s.objective,
            "description": s.description, "requires_wordlist": s.requires_wordlist, "defense": s.defense,
        }
        for s in SCENARIOS.values()
    ]
