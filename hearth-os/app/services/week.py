from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models import Household, MealPlan, Person
from app.services.food_law import contains_symptom_word
from app.services.meals import build_meals, get_or_create_plan, monday_on_or_before
from app.services.quiet import copy_quiet_onto_plan
from app.services.shopping import build_shopping_plan, persist_cart


def persist_week(
    session: Session,
    household: Household,
    people: list[Person],
    today: date,
    week_start: date | None = None,
) -> MealPlan:
    week_start = week_start or monday_on_or_before(today)
    plan_row = get_or_create_plan(session, household, week_start)
    if contains_symptom_word(plan_row.notes or ""):
        plan_row.notes = ""
    build_meals(session, plan_row, people, freezer_share=household.freezer_share or "none")
    cart = build_shopping_plan(session, household, week_start, today)
    copy_quiet_onto_plan(session, household.id, week_start, cart, today)
    persist_cart(session, plan_row, cart)
    session.commit()
    session.refresh(plan_row)
    return plan_row
