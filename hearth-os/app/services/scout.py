from __future__ import annotations

from datetime import date
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.ads import record_ad_fetch


def fetch_tops_ad_text(session: Session, timeout: float = 12.0) -> dict:
    """Best-effort raw fetch. Never treat the HTML as gospel prices."""
    settings = get_settings()
    url = settings.TOPS_AD_URL
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "HearthOS/1.0 (household kitchen; +local)"},
        )
        ok = response.status_code == 200
        text = response.text if ok else f"http {response.status_code}"
        row = record_ad_fetch(session, "tops", url, ok, text)
        session.commit()
        return {"ok": ok, "id": row.id, "excerpt": row.text_excerpt[:400]}
    except httpx.HTTPError as exc:
        row = record_ad_fetch(session, "tops", url, False, str(exc))
        session.commit()
        return {"ok": False, "id": row.id, "excerpt": row.text_excerpt[:400]}


def parse_optional_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    return date.fromisoformat(raw)
