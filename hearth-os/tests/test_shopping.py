from datetime import date, timedelta

from app.models import CatalogItem, Household, Person, ShoppingItem
from app.services.ads import upsert_ad
from app.services.food_law import STAPLE_RICE_KEY
from app.services.meals import monday_on_or_before
from app.services.shopping import WEEK_QTY, build_shopping_plan, weekly_spend
from app.services.week import persist_week


def test_week_start_is_monday():
    wednesday = date(2026, 8, 19)
    assert monday_on_or_before(wednesday) == date(2026, 8, 17)
    assert monday_on_or_before(wednesday).weekday() == 0


def test_chicken_sale_live_goes_to_tops(db_session):
    household = db_session.query(Household).first()
    today = date(2026, 8, 18)
    upsert_ad(
        db_session,
        household.id,
        "chicken_quarters",
        "tops",
        0.99,
        sale_ends=date(2026, 8, 22),
        source="manual",
    )
    plan = build_shopping_plan(db_session, household, monday_on_or_before(today), today)
    chicken = next(line for line in plan.lines if line.catalog_key == "chicken_quarters")
    assert chicken.store == "tops"
    assert chicken.unit_price == 0.99
    assert chicken.note == ""


def test_chicken_expired_sale_is_not_live(db_session):
    household = db_session.query(Household).first()
    today = date(2026, 8, 23)
    upsert_ad(
        db_session,
        household.id,
        "chicken_quarters",
        "tops",
        1.79,
        sale_ends=date(2026, 8, 22),
        source="manual",
    )
    plan = build_shopping_plan(db_session, household, monday_on_or_before(today), today)
    chicken = next(line for line in plan.lines if line.catalog_key == "chicken_quarters")
    assert chicken.note == "not live"
    assert chicken.store != "tops"


def test_jasmine_rice_is_only_bulk_rice_and_no_ground_beef(db_session):
    from app.models import CatalogItem

    keys = {row.key for row in db_session.query(CatalogItem).all()}
    assert STAPLE_RICE_KEY in keys
    assert "ground_beef" not in keys
    rice_keys = {k for k in keys if "rice" in k}
    assert rice_keys == {STAPLE_RICE_KEY}
    assert "quinoa" in keys
    household = db_session.query(Household).first()
    plan = build_shopping_plan(db_session, household, date(2026, 8, 17), date(2026, 8, 18))
    assert "quinoa" not in {line.catalog_key for line in plan.lines}
    assert "jasmine_rice" in {line.catalog_key for line in plan.lines}
    assert "potatoes" in {line.catalog_key for line in plan.lines}


def test_store_split_and_cap(db_session):
    household = db_session.query(Household).first()
    people = db_session.query(Person).all()
    plan = persist_week(db_session, household, people, date(2026, 8, 18), date(2026, 8, 17))
    stores = {item.store for item in plan.items}
    assert "aldi" in stores
    assert "gfs" in stores
    total = weekly_spend(plan.items)
    assert total <= household.weekly_cap or total < 130
    assert total > 40
