from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.db import db_writable

router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    db_ok = db_writable()
    grok = settings.grok_configured()
    return {
        "ok": db_ok,
        "db": db_ok,
        "grok": grok,
        "version": settings.APP_VERSION,
    }
