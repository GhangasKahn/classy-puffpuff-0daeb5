from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Header, HTTPException

from app.config import get_settings
from app.db import get_session_factory
from app.models import Household, Person
from app.services.scout import fetch_tops_ad_text
from app.services.week import persist_week

router = APIRouter()


@router.post("/internal/scout")
def internal_scout(x_cron_token: str | None = Header(default=None, alias="X-Cron-Token")):
    settings = get_settings()
    token = settings.CRON_TOKEN.strip()
    if not token or x_cron_token != token:
        raise HTTPException(status_code=401, detail="cron token rejected")
    session = get_session_factory()()
    try:
        fetch_tops_ad_text(session)
        household = session.query(Household).first()
        if household is not None:
            people = session.query(Person).filter(Person.household_id == household.id).all()
            persist_week(session, household, people, date.today())
        return {"ok": True}
    finally:
        session.close()
