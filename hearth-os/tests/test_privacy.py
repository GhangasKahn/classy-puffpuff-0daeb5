from __future__ import annotations

from datetime import date

from app.services.crypto import decrypt, encrypt, house_scope, private_scope
from app.services.food_law import contains_symptom_word
from app.services.quiet import infer_quiet_adds, public_ack_for
from app.services.rooms import post_house, post_private, read_house, read_private


def test_encrypt_decrypt_isolation():
    house = house_scope(1)
    private_one = private_scope(1, 1)
    private_two = private_scope(1, 2)
    token = encrypt(private_one, "Oak\nstomach flu")
    assert decrypt(private_one, token).endswith("stomach flu")
    assert decrypt(private_two, token) == ""
    assert decrypt(house, token) == ""


def test_house_post_does_not_persist_person_id(db_session):
    from app.models import Household, VaultMessage

    household = db_session.query(Household).first()
    post_house(db_session, household.id, "Build this week.", "Oak")
    db_session.commit()
    row = db_session.query(VaultMessage).filter(VaultMessage.room == "house").first()
    assert row is not None
    assert row.person_id is None
    messages = read_house(db_session, household.id)
    assert any("Build this week." in m.body for m in messages)
    assert "gAAAA" not in messages[0].body


def test_private_reader_is_scoped(db_session):
    from app.models import Household, Person

    household = db_session.query(Household).first()
    people = db_session.query(Person).order_by(Person.id).all()
    a, b = people[0], people[1]
    post_private(db_session, household.id, a.id, "private note from a", a.alias)
    db_session.commit()
    mine = read_private(db_session, household.id, a.id)
    other = read_private(db_session, household.id, b.id)
    assert any("private note from a" in m.body for m in mine)
    assert all("private note from a" not in m.body for m in other)


def test_quiet_does_not_write_flu_into_list_or_notes(db_session):
    from datetime import date

    from app.models import Household, MealPlan, Person, ShoppingItem
    from app.services.meals import monday_on_or_before
    from app.services.quiet import record_quiet_needs
    from app.services.week import persist_week

    household = db_session.query(Household).first()
    person = db_session.query(Person).first()
    adds = infer_quiet_adds("I have the stomach flu and a headache")
    assert {a.catalog_key for a in adds} >= {"bananas", "broth", "ginger"}
    ack = public_ack_for(adds)
    assert not contains_symptom_word(ack)
    week_start = monday_on_or_before(date.today())
    record_quiet_needs(db_session, household.id, week_start, person.id, adds)
    persist_week(db_session, household, db_session.query(Person).all(), date.today(), week_start)
    plan = (
        db_session.query(MealPlan)
        .filter(MealPlan.household_id == household.id, MealPlan.week_start == week_start)
        .one()
    )
    assert not contains_symptom_word(plan.notes or "")
    names = [i.name.lower() for i in plan.items]
    joined = " ".join(names)
    assert "flu" not in joined
    assert "headache" not in joined
    assert any(i.name == "Bananas" for i in plan.items)
    assert any(i.name == "Chicken broth" for i in plan.items)
