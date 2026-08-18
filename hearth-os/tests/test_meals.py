from datetime import date
import re

from app.models import Household, Person
from app.services.food_law import contains_symptom_word, is_banned
from app.services.meals import WEEK_MENU
from app.services.week import persist_week


def test_week_is_mountain_table_not_clinic(db_session):
    household = db_session.query(Household).first()
    people = db_session.query(Person).all()
    plan = persist_week(db_session, household, people, date(2026, 8, 18), date(2026, 8, 17))
    keys = {item.catalog_key for item in plan.items}
    names = " ".join(item.name.lower() for item in plan.items)
    titles = " ".join(m.title.lower() for m in plan.meals)
    notes = " ".join(m.cook_notes.lower() for m in plan.meals)
    blob = titles + " " + notes + " " + names

    assert "lamb" in keys
    assert "flour" in keys
    assert "jasmine_rice" in keys
    assert "potatoes" in keys
    assert "yogurt" in keys
    assert "chickpeas_dry" in keys
    assert "lentils" in keys
    assert "ground_beef" not in keys
    assert "venison" not in keys
    assert re.search(r"\bliver\b", blob) is None
    assert "kerrygold" not in blob
    assert "keto" not in blob
    assert "probiotic" not in blob
    assert "lactobacillus" not in blob
    assert not contains_symptom_word(blob)
    assert is_banned(blob)[0] is False
    assert any("cold ferment" in m.cook_notes.lower() for m in plan.meals)
    assert any("pita" in (m.title + m.cook_notes).lower() for m in plan.meals)

    total = round(sum(i.qty * i.unit_price for i in plan.items), 2)
    assert total <= household.weekly_cap or total < 130
    household = db_session.query(Household).first()
    people = db_session.query(Person).all()
    plan = persist_week(db_session, household, people, date(2026, 8, 18), date(2026, 8, 17))
    keys = {item.catalog_key for item in plan.items}
    names = " ".join(item.name.lower() for item in plan.items)
    titles = " ".join(m.title.lower() for m in plan.meals)
    notes = " ".join(m.cook_notes.lower() for m in plan.meals)
    blob = titles + " " + notes + " " + names

    assert "lamb" in keys
    assert "flour" in keys
    assert "jasmine_rice" in keys
    assert "potatoes" in keys
    assert "yogurt" in keys
    assert "chickpeas_dry" in keys
    assert "lentils" in keys
    assert "ground_beef" not in keys
    assert "venison" not in keys
    assert "liver" not in blob
    assert "kerrygold" not in blob
    assert "keto" not in blob
    assert "probiotic" not in blob
    assert "digest" not in blob
    assert not contains_symptom_word(blob)
    assert is_banned(blob)[0] is False
    assert any("cold ferment" in m.cook_notes.lower() for m in plan.meals)
    assert any("pita" in (m.title + m.cook_notes).lower() for m in plan.meals)

    total = round(sum(i.qty * i.unit_price for i in plan.items), 2)
    assert total <= household.weekly_cap or total < 130


def test_menu_source_has_no_medical_claims():
    text = str(WEEK_MENU).lower()
    for word in ("therapeutic", "anti-cancer", "cures", "probiotic", "lactobacillus"):
        assert word not in text
