from __future__ import annotations

from app.models import Person, Recipe, VaultMessage
from app.services.food_law import contains_symptom_word


def test_login_shows_aliases_only(client, db_session):
    person = db_session.query(Person).first()
    person.legal_name = "Legal Name Must Stay Hidden"
    db_session.commit()
    html = client.get("/login").text
    assert person.alias in html
    assert "Legal Name Must Stay Hidden" not in html


def test_chat_private_without_session_goes_house(client):
    response = client.get("/chat?room=private", follow_redirects=False)
    assert response.status_code == 303
    assert "room=house" in response.headers["location"]


def test_target_person_query_is_ignored(logged_in, client, db_session):
    people = db_session.query(Person).order_by(Person.id).all()
    other = people[1]
    html = client.get(f"/rooms?room=private&target_person_id={other.id}").text
    assert "gAAAA" not in html
    assert other.legal_name not in html or not other.legal_name


def test_person_two_cannot_see_person_one_private(client, db_session):
    people = db_session.query(Person).order_by(Person.id).all()
    a, b = people[0], people[1]
    client.post("/login", data={"pin": "4829", "person_id": str(a.id)})
    client.post("/rooms", data={"room": "private", "body": "I have the stomach flu"})
    html_a = client.get("/rooms?room=private").text
    assert "stomach flu" in html_a
    client.post("/logout")
    client.post("/login", data={"pin": "4829", "person_id": str(b.id)})
    html_b = client.get("/rooms?room=private").text
    assert "stomach flu" not in html_b
    html_house = client.get("/rooms?room=house").text
    assert "stomach flu" not in html_house
    assert "gAAAA" not in html_b
    assert "gAAAA" not in html_house


def test_private_recipe_is_not_a_recipe_row(logged_in, client, db_session):
    before = db_session.query(Recipe).count()
    client.post(
        "/recipes",
        data={"title": "Private paste", "body": "rice and potatoes", "room": "private"},
    )
    db_session.expire_all()
    assert db_session.query(Recipe).count() == before
    private_rows = db_session.query(VaultMessage).filter(VaultMessage.room == "private").all()
    assert private_rows
