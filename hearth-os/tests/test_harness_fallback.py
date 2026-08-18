from app.agents.harness import deterministic_handle
from app.models import Household, MealPlan, Person, Recipe
from app.services.food_law import HOUSE_LAW_REPLY, is_banned


def test_is_banned_kerrygold_liver_keto():
    assert is_banned("spread Kerrygold on potatoes")[0] is True
    assert is_banned("chicken liver pâté")[0] is True
    assert is_banned("strict keto dinner")[0] is True
    assert is_banned("jasmine rice and roast chicken")[0] is False
    assert is_banned("artichoke hearts")[0] is False


def test_harness_fallback_builds_week_without_api_key(db_session, monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "")
    from app.config import clear_settings_cache

    clear_settings_cache()
    person = db_session.query(Person).first()
    reply = deterministic_handle(db_session, person, "build this week", "house")
    assert "Kitchen" in reply or "week" in reply.lower()
    household = db_session.query(Household).first()
    plans = db_session.query(MealPlan).filter(MealPlan.household_id == household.id).all()
    assert plans
    assert plans[0].items


def test_house_recipe_rejects_banned(logged_in, client, db_session):
    response = client.post(
        "/recipes",
        data={"title": "Keto liver", "body": "keto with liver and Kerrygold", "room": "house"},
    )
    assert HOUSE_LAW_REPLY in response.text
    assert db_session.query(Recipe).count() == 0
