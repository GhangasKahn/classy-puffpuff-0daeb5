from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.models import CatalogItem, MealPlan, QuietNeed, ShoppingItem
from app.services.ads import resolve_catalog_item
from app.services.food_law import contains_symptom_word
from app.services.shopping import GFS_WEEKLY, CartLine, ShoppingPlan, merge_line

# Keyword map only. No medications. No branded electrolyte drinks.
KEYWORD_ADDS: list[tuple[tuple[str, ...], list[tuple[str, float]]]] = [
    (
        ("stomach", "flu", "vomit", "diarrhea", "nausea"),
        [("bananas", 2.0), ("jasmine_rice", 0.0), ("broth", 2.0), ("ginger", 0.25)],
    ),
    (
        ("headache", "migraine"),
        [("ginger", 0.25), ("apples", 2.0)],
    ),
    (
        ("constipat",),
        [("apples", 2.0), ("cabbage", 1.0)],
    ),
]

ALLOWED_QUIET_KEYS = frozenset(
    {"bananas", "jasmine_rice", "broth", "ginger", "apples", "cabbage"}
)

PUBLIC_ACK = "Kitchen extras added to the list."


@dataclass(frozen=True)
class QuietAdd:
    catalog_key: str
    qty: float


def infer_quiet_adds(text: str) -> list[QuietAdd]:
    blob = (text or "").lower()
    found: dict[str, float] = {}
    for keywords, adds in KEYWORD_ADDS:
        if any(word in blob for word in keywords):
            for key, qty in adds:
                if key not in ALLOWED_QUIET_KEYS:
                    continue
                if qty <= 0:
                    continue
                found[key] = found.get(key, 0.0) + qty
    return [QuietAdd(key, qty) for key, qty in found.items()]


def public_ack_for(_adds: list[QuietAdd]) -> str:
    ack = PUBLIC_ACK
    assert not contains_symptom_word(ack)
    return ack


def apply_quiet_to_plan(
    session: Session,
    household_id: int,
    plan: ShoppingPlan,
    adds: list[QuietAdd],
    today: date,
) -> ShoppingPlan:
    catalog = {
        row.key: row
        for row in session.query(CatalogItem).filter(CatalogItem.household_id == household_id)
    }
    for add in adds:
        if add.catalog_key in GFS_WEEKLY:
            continue
        item = catalog.get(add.catalog_key)
        if item is None:
            continue
        resolved = resolve_catalog_item(session, item, today)
        merge_line(
            plan,
            CartLine(
                catalog_key=resolved.catalog_key,
                name=resolved.name,
                qty=add.qty,
                unit=resolved.unit,
                store=resolved.store,
                unit_price=resolved.price,
                source="quiet",
                protein_g=resolved.protein_g,
                kcal=resolved.kcal,
            ),
        )
    return plan


def record_quiet_needs(
    session: Session,
    household_id: int,
    week_start: date,
    person_id: int,
    adds: list[QuietAdd],
) -> str:
    ack = public_ack_for(adds)
    for add in adds:
        session.add(
            QuietNeed(
                household_id=household_id,
                week_start=week_start,
                person_id=person_id,
                catalog_key=add.catalog_key,
                qty=add.qty,
                public_ack=ack,
            )
        )
    session.flush()
    return ack


def quiet_qty_for_week(
    session: Session, household_id: int, week_start: date
) -> dict[str, float]:
    rows = (
        session.query(QuietNeed)
        .filter(QuietNeed.household_id == household_id, QuietNeed.week_start == week_start)
        .all()
    )
    qty: dict[str, float] = {}
    for row in rows:
        qty[row.catalog_key] = qty.get(row.catalog_key, 0.0) + row.qty
    return qty


def copy_quiet_onto_plan(
    session: Session,
    household_id: int,
    week_start: date,
    plan: ShoppingPlan,
    today: date,
) -> None:
    adds = [QuietAdd(key, qty) for key, qty in quiet_qty_for_week(session, household_id, week_start).items()]
    apply_quiet_to_plan(session, household_id, plan, adds, today)


def shopping_names_are_food_only(items: list[ShoppingItem]) -> bool:
    return all(not contains_symptom_word(item.name) for item in items)


def meal_notes_are_clean(plan: MealPlan) -> bool:
    return not contains_symptom_word(plan.notes or "")
