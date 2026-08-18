from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable

from sqlalchemy.orm import Session

from app.models import CatalogItem, Household, MealPlan, Person, ShoppingItem
from app.services.ads import ResolvedPrice, resolve_catalog_item
from app.services.food_law import STAPLE_RICE_KEY

# Seed SKUs for a 7-day sheet feeding three adults. Prices are seeds, not live ads.
# Seed SKUs for a 7-day sheet feeding three adults. Prices are seeds, not live ads.
# Mountain table + Mediterranean, homemade bread. Jasmine rice and potatoes stay.
# Game meat is not auto-bought (no invented store price). Use it if you already have it.
WEEK_QTY: dict[str, float] = {
    "chicken_quarters": 8.0,
    "lamb": 3.0,
    "jasmine_rice": 2.0,
    "potatoes": 3.0,
    "eggs": 3.0,
    "cabbage": 2.0,
    "onions": 1.0,
    "carrots": 1.0,
    "butter": 1.0,
    "milk": 2.0,
    "beans_canned": 4.0,
    "oats": 1.0,
    "yogurt": 2.0,
    "olive_oil": 1.0,
    "flour": 1.0,
    "chickpeas_dry": 2.0,
    "lentils": 2.0,
    "cucumbers": 3.0,
    "tomatoes": 3.0,
    "garlic": 2.0,
    "lemons": 1.0,
    "bananas": 2.0,
    "apples": 1.0,
    "broth": 1.0,
}

# Quinoa is optional 1 lb, never the bulk rice, never auto-added as a staple.
OPTIONAL_KEYS = frozenset({"quinoa"})


@dataclass
class CartLine:
    catalog_key: str
    name: str
    qty: float
    unit: str
    store: str
    unit_price: float
    source: str
    note: str = ""
    protein_g: float = 0.0
    kcal: float = 0.0

    @property
    def line_total(self) -> float:
        return round(self.qty * self.unit_price, 2)


@dataclass
class ShoppingPlan:
    week_start: date
    lines: list[CartLine] = field(default_factory=list)
    cap: float = 110.0

    @property
    def total(self) -> float:
        return round(sum(line.line_total for line in self.lines), 2)

    @property
    def over_cap(self) -> bool:
        return self.total > self.cap

    def by_store(self) -> dict[str, list[CartLine]]:
        grouped: dict[str, list[CartLine]] = defaultdict(list)
        for line in self.lines:
            grouped[line.store].append(line)
        return dict(grouped)

    def store_totals(self) -> dict[str, float]:
        return {
            store: round(sum(line.line_total for line in lines), 2)
            for store, lines in self.by_store().items()
        }

    def protein_estimate(self) -> float:
        return round(sum(line.protein_g * line.qty for line in self.lines), 1)


def catalog_map(session: Session, household_id: int) -> dict[str, CatalogItem]:
    rows = session.query(CatalogItem).filter(CatalogItem.household_id == household_id).all()
    return {row.key: row for row in rows}


def build_shopping_plan(
    session: Session,
    household: Household,
    week_start: date,
    today: date,
    extra_qty: dict[str, float] | None = None,
    include_optional: Iterable[str] = (),
) -> ShoppingPlan:
    items = catalog_map(session, household.id)
    qty = dict(WEEK_QTY)
    if extra_qty:
        for key, amount in extra_qty.items():
            qty[key] = qty.get(key, 0.0) + amount
    for key in include_optional:
        if key in OPTIONAL_KEYS and key not in qty:
            qty[key] = 1.0

    plan = ShoppingPlan(week_start=week_start, cap=household.weekly_cap)
    rice_seen = False
    for key, amount in qty.items():
        catalog = items.get(key)
        if catalog is None:
            continue
        if key in {"white_rice", "brown_rice", "basmati"}:
            continue
        resolved = resolve_catalog_item(session, catalog, today)
        if resolved.catalog_key == STAPLE_RICE_KEY:
            rice_seen = True
        plan.lines.append(
            CartLine(
                catalog_key=resolved.catalog_key,
                name=resolved.name,
                qty=amount,
                unit=resolved.unit,
                store=resolved.store,
                unit_price=resolved.price,
                source="week",
                note=resolved.note,
                protein_g=resolved.protein_g,
                kcal=resolved.kcal,
            )
        )
    if not rice_seen:
        rice = items.get(STAPLE_RICE_KEY)
        if rice is not None:
            resolved = resolve_catalog_item(session, rice, today)
            plan.lines.insert(
                0,
                CartLine(
                    catalog_key=resolved.catalog_key,
                    name=resolved.name,
                    qty=2.0,
                    unit=resolved.unit,
                    store=resolved.store,
                    unit_price=resolved.price,
                    source="week",
                    protein_g=resolved.protein_g,
                    kcal=resolved.kcal,
                ),
            )
    return plan


def merge_line(plan: ShoppingPlan, incoming: CartLine) -> CartLine:
    for line in plan.lines:
        if line.catalog_key == incoming.catalog_key:
            line.qty += incoming.qty
            if incoming.source == "quiet":
                line.source = "quiet" if line.source == "quiet" else line.source
            return line
    plan.lines.append(incoming)
    return incoming


def persist_cart(session: Session, meal_plan: MealPlan, plan: ShoppingPlan) -> None:
    existing_checked = {
        row.catalog_key: row.checked
        for row in meal_plan.items
    }
    meal_plan.items.clear()
    session.flush()
    for line in plan.lines:
        session.add(
            ShoppingItem(
                meal_plan_id=meal_plan.id,
                catalog_key=line.catalog_key,
                name=line.name,
                qty=line.qty,
                unit=line.unit,
                store=line.store,
                unit_price=line.unit_price,
                checked=existing_checked.get(line.catalog_key, False),
                source=line.source,
                note=line.note,
            )
        )
    session.flush()


def house_has_cancer_track(people: list[Person]) -> bool:
    return any(person.cancer_track for person in people)


def house_has_soft_food(people: list[Person]) -> bool:
    return any(person.soft_food for person in people)
