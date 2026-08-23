from datetime import date

from app.models import Household, MealPlan, Person, ShoppingItem
from app.services.food_law import contains_symptom_word
from app.services.meals import monday_on_or_before
from app.services.quiet import infer_quiet_adds, public_ack_for
from app.services.shopping import CartLine, ShoppingPlan, merge_line
from app.services.week import persist_week


def test_public_ack_has_no_symptom_words():
    adds = infer_quiet_adds("stomach flu vomit diarrhea nausea headache migraine constipation")
    ack = public_ack_for(adds)
    for word in ("flu", "vomit", "headache", "cancer"):
        assert word not in ack.lower()
    assert not contains_symptom_word(ack)


def test_quiet_bumps_banana_qty_instead_of_skipping():
    plan = ShoppingPlan(week_start=date(2026, 8, 17))
    plan.lines.append(
        CartLine(
            catalog_key="bananas",
            name="Bananas",
            qty=2.0,
            unit="lb",
            store="aldi",
            unit_price=0.49,
            source="week",
        )
    )
    merge_line(
        plan,
        CartLine(
            catalog_key="bananas",
            name="Bananas",
            qty=2.0,
            unit="lb",
            store="aldi",
            unit_price=0.49,
            source="quiet",
        ),
    )
    bananas = [line for line in plan.lines if line.catalog_key == "bananas"]
    assert len(bananas) == 1
    assert bananas[0].qty == 4.0


def test_persist_week_keeps_quiet_needs(db_session):
    from app.services.quiet import record_quiet_needs

    household = db_session.query(Household).first()
    person = db_session.query(Person).first()
    week_start = date(2026, 8, 17)
    adds = infer_quiet_adds("nausea and stomach flu")
    record_quiet_needs(db_session, household.id, week_start, person.id, adds)
    persist_week(db_session, household, db_session.query(Person).all(), date(2026, 8, 18), week_start)
    persist_week(db_session, household, db_session.query(Person).all(), date(2026, 8, 18), week_start)
    plan = (
        db_session.query(MealPlan)
        .filter(MealPlan.household_id == household.id, MealPlan.week_start == week_start)
        .one()
    )
    names = {item.name for item in plan.items}
    assert "Bananas" in names
    assert "Fresh ginger" in names
    assert all(not contains_symptom_word(item.name) for item in plan.items)
