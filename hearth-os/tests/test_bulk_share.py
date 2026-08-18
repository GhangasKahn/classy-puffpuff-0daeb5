from datetime import date

from app.models import Household, Person
from app.services.food_law import is_banned
from app.services.shopping import SHARE_DROPS_LAMB, haul_spend, weekly_spend
from app.services.week import persist_week


def test_vegetable_oil_is_banned():
    assert is_banned("fry in vegetable oil")[0] is True
    assert is_banned("canola oil drizzle")[0] is True
    assert is_banned("cold-pressed olive oil")[0] is False
    assert is_banned("avocado oil")[0] is False


def test_cart_has_cold_pressed_oils_not_vegetable(db_session):
    household = db_session.query(Household).first()
    people = db_session.query(Person).all()
    plan = persist_week(db_session, household, people, date(2026, 8, 18), date(2026, 8, 17))
    keys = {item.catalog_key for item in plan.items}
    names = " ".join(item.name.lower() for item in plan.items)
    assert "olive_oil" in keys
    assert "avocado_oil" in keys
    assert "oil" not in keys
    assert "vegetable oil" not in names
    assert any(item.store == "gfs" for item in plan.items)


def test_gfs_haul_is_not_in_weekly_cap(db_session):
    household = db_session.query(Household).first()
    people = db_session.query(Person).all()
    household.bulk_weeks = 4
    plan = persist_week(db_session, household, people, date(2026, 8, 18), date(2026, 8, 17))
    week = weekly_spend(plan.items)
    haul = haul_spend(plan.items)
    assert week <= household.weekly_cap or week < 130
    rice = next(i for i in plan.items if i.catalog_key == "jasmine_rice")
    assert rice.source == "gfs_bulk"
    assert rice.qty == 8.0


def test_elk_share_drops_grocery_lamb(db_session):
    household = db_session.query(Household).first()
    people = db_session.query(Person).all()
    household.freezer_share = "elk"
    household.share_cost = 480
    household.share_weeks = 12
    household.freezer_lb = 40
    assert household.freezer_share in SHARE_DROPS_LAMB
    plan = persist_week(db_session, household, people, date(2026, 8, 18), date(2026, 8, 17))
    keys = {item.catalog_key for item in plan.items}
    assert "lamb" not in keys
    notes = " ".join(m.cook_notes.lower() for m in plan.meals)
    assert "freezer share" in notes
