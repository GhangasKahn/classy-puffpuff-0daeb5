from __future__ import annotations

from datetime import date
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Ad, CatalogItem, Household, Person, Recipe
from app.services.ads import upsert_ad
from app.services.food_law import HOUSE_LAW_REPLY, contains_symptom_word, is_banned
from app.services.meals import monday_on_or_before
from app.services.quiet import infer_quiet_adds, record_quiet_needs
from app.services.scout import fetch_tops_ad_text, parse_optional_date
from app.services.week import persist_week

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_household_state",
            "description": "Aliases, flags, weekly cap. No legal names. No private notes.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_ads",
            "description": "Return catalog keys with latest ad or seed price.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_tops_circular",
            "description": "Best-effort fetch of the Tops weekly ad page. Stores raw excerpt only.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "upsert_ad",
            "description": "Correct a seed price. catalog_key must already exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "catalog_key": {"type": "string"},
                    "store": {"type": "string"},
                    "price": {"type": "number"},
                    "sale_ends": {"type": "string", "description": "YYYY-MM-DD or empty"},
                },
                "required": ["catalog_key", "store", "price"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "build_week",
            "description": "Rebuild the Monday-start week from deterministic engines.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_quiet_from_private_text",
            "description": "Private room only. Infer bland SKUs from private text. List shows food names only.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
]


def _household(session: Session) -> Household:
    row = session.query(Household).first()
    assert row is not None
    return row


def get_household_state(session: Session) -> dict[str, Any]:
    household = _household(session)
    people = session.query(Person).filter(Person.household_id == household.id).all()
    return {
        "aliases": [p.alias for p in people],
        "weekly_cap": household.weekly_cap,
        "energy_first_count": sum(1 for p in people if p.cancer_track),
        "soft_food_count": sum(1 for p in people if p.soft_food),
        "week_start": monday_on_or_before(date.today()).isoformat(),
    }


def get_current_ads(session: Session) -> list[dict[str, Any]]:
    household = _household(session)
    items = session.query(CatalogItem).filter(CatalogItem.household_id == household.id).all()
    ads = session.query(Ad).filter(Ad.household_id == household.id).all()
    latest: dict[str, Ad] = {}
    for ad in ads:
        prev = latest.get(ad.catalog_key)
        if prev is None or ad.updated_at >= prev.updated_at:
            latest[ad.catalog_key] = ad
    out = []
    for item in items:
        ad = latest.get(item.key)
        out.append(
            {
                "key": item.key,
                "name": item.name,
                "store": ad.store if ad else item.default_store,
                "price": ad.price if ad else item.typical_price,
                "sale_ends": (ad.sale_ends.isoformat() if ad and ad.sale_ends else (
                    item.sale_ends.isoformat() if item.sale_ends else None
                )),
                "source": "ad" if ad else "catalog",
            }
        )
    return out


def tool_fetch_tops_circular(session: Session) -> dict[str, Any]:
    return fetch_tops_ad_text(session)


def tool_upsert_ad(
    session: Session,
    catalog_key: str,
    store: str,
    price: float,
    sale_ends: Optional[str] = None,
) -> dict[str, Any]:
    household = _household(session)
    item = (
        session.query(CatalogItem)
        .filter(CatalogItem.household_id == household.id, CatalogItem.key == catalog_key)
        .one_or_none()
    )
    if item is None:
        return {"ok": False, "error": "unknown catalog key"}
    row = upsert_ad(
        session,
        household.id,
        catalog_key,
        store,
        float(price),
        parse_optional_date(sale_ends),
        source="manual",
    )
    session.commit()
    return {
        "ok": True,
        "key": row.catalog_key,
        "store": row.store,
        "price": row.price,
        "sale_ends": row.sale_ends.isoformat() if row.sale_ends else None,
    }


def tool_build_week(session: Session) -> dict[str, Any]:
    household = _household(session)
    people = session.query(Person).filter(Person.household_id == household.id).all()
    plan = persist_week(session, household, people, date.today())
    total = round(sum(i.qty * i.unit_price for i in plan.items), 2)
    return {
        "ok": True,
        "week_start": plan.week_start.isoformat(),
        "item_count": len(plan.items),
        "total": total,
        "cap": household.weekly_cap,
    }


def tool_apply_quiet_from_private_text(
    session: Session,
    person_id: int,
    text: str,
    room: str,
) -> dict[str, Any]:
    if room != "private":
        return {"ok": False, "error": "quiet needs are private-room only"}
    household = _household(session)
    adds = infer_quiet_adds(text)
    if not adds:
        return {"ok": True, "added": [], "ack": ""}
    week_start = monday_on_or_before(date.today())
    ack = record_quiet_needs(session, household.id, week_start, person_id, adds)
    people = session.query(Person).filter(Person.household_id == household.id).all()
    persist_week(session, household, people, date.today(), week_start)
    return {
        "ok": True,
        "added": [a.catalog_key for a in adds],
        "ack": ack,
    }


def maybe_store_house_recipe(session: Session, household_id: int, text: str, room: str) -> Optional[str]:
    if room != "house":
        return None
    banned, _reason = is_banned(text)
    if banned:
        return HOUSE_LAW_REPLY
    title = "House recipe"
    first = text.strip().splitlines()[0][:80] if text.strip() else title
    session.add(Recipe(household_id=household_id, title=first, body=text))
    session.flush()
    return None


def redact_for_house(payload: Any) -> Any:
    if isinstance(payload, str) and contains_symptom_word(payload):
        return "[redacted]"
    if isinstance(payload, dict):
        return {k: redact_for_house(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [redact_for_house(v) for v in payload]
    return payload


def dispatch_tool(
    session: Session,
    name: str,
    arguments: dict[str, Any],
    *,
    room: str,
    person_id: int,
) -> Any:
    if name == "get_household_state":
        result = get_household_state(session)
    elif name == "get_current_ads":
        result = get_current_ads(session)
    elif name == "fetch_tops_circular":
        result = tool_fetch_tops_circular(session)
    elif name == "upsert_ad":
        result = tool_upsert_ad(
            session,
            arguments.get("catalog_key", ""),
            arguments.get("store", "aldi"),
            float(arguments.get("price", 0)),
            arguments.get("sale_ends"),
        )
    elif name == "build_week":
        result = tool_build_week(session)
    elif name == "apply_quiet_from_private_text":
        result = tool_apply_quiet_from_private_text(
            session, person_id, arguments.get("text", ""), room
        )
    else:
        result = {"ok": False, "error": "unknown tool"}
    if room == "house":
        return redact_for_house(result)
    return result
