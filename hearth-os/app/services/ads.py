from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Ad, AdFetch, CatalogItem


CHICKEN_SALE_MAX = 1.29
CHICKEN_KEY = "chicken_quarters"


@dataclass(frozen=True)
class ResolvedPrice:
    catalog_key: str
    name: str
    store: str
    unit: str
    price: float
    protein_g: float
    kcal: float
    sale_ends: Optional[date]
    note: str
    source: str


def latest_ad(session: Session, household_id: int, catalog_key: str) -> Optional[Ad]:
    return (
        session.query(Ad)
        .filter(Ad.household_id == household_id, Ad.catalog_key == catalog_key)
        .order_by(Ad.updated_at.desc(), Ad.id.desc())
        .first()
    )


def upsert_ad(
    session: Session,
    household_id: int,
    catalog_key: str,
    store: str,
    price: float,
    sale_ends: Optional[date] = None,
    source: str = "manual",
) -> Ad:
    row = (
        session.query(Ad)
        .filter(
            Ad.household_id == household_id,
            Ad.catalog_key == catalog_key,
            Ad.store == store,
        )
        .order_by(Ad.id.desc())
        .first()
    )
    if row is None:
        row = Ad(
            household_id=household_id,
            catalog_key=catalog_key,
            store=store,
            price=price,
            sale_ends=sale_ends,
            source=source,
        )
        session.add(row)
    else:
        row.price = price
        row.sale_ends = sale_ends
        row.source = source
    session.flush()
    return row


def record_ad_fetch(
    session: Session,
    store: str,
    url: str,
    ok: bool,
    text: str,
) -> AdFetch:
    excerpt = (text or "")[:4000]
    row = AdFetch(store=store, url=url, ok=ok, text_excerpt=excerpt)
    session.add(row)
    session.flush()
    return row


def _chicken_store_and_note(
    price: float,
    sale_ends: Optional[date],
    fallback_store: str,
    today: date,
) -> tuple[str, str]:
    live = sale_ends is None or sale_ends >= today
    if live and price <= CHICKEN_SALE_MAX:
        return "tops", ""
    if not live:
        return fallback_store, "not live"
    return fallback_store, ""


def resolve_catalog_item(
    session: Session,
    item: CatalogItem,
    today: date,
) -> ResolvedPrice:
    ad = latest_ad(session, item.household_id, item.key)
    if ad is not None:
        store = ad.store
        note = ""
        if item.key == CHICKEN_KEY:
            store, note = _chicken_store_and_note(
                ad.price, ad.sale_ends, item.default_store, today
            )
        return ResolvedPrice(
            catalog_key=item.key,
            name=item.name,
            store=store,
            unit=item.unit,
            price=ad.price,
            protein_g=item.protein_g,
            kcal=item.kcal,
            sale_ends=ad.sale_ends,
            note=note,
            source="ad",
        )

    store = item.default_store
    note = ""
    if item.key == CHICKEN_KEY:
        store, note = _chicken_store_and_note(
            item.typical_price, item.sale_ends, item.default_store, today
        )
        if note == "not live":
            # After the seed sale window, do not assume $0.99 / Tops.
            return ResolvedPrice(
                catalog_key=item.key,
                name=item.name,
                store=item.default_store if item.sale_ends else store,
                unit=item.unit,
                price=item.typical_price,
                protein_g=item.protein_g,
                kcal=item.kcal,
                sale_ends=item.sale_ends,
                note="not live",
                source="catalog",
            )
    return ResolvedPrice(
        catalog_key=item.key,
        name=item.name,
        store=store,
        unit=item.unit,
        price=item.typical_price,
        protein_g=item.protein_g,
        kcal=item.kcal,
        sale_ends=item.sale_ends,
        note=note,
        source="catalog",
    )
