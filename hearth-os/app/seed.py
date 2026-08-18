from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base, get_engine, get_session_factory
from app.models import Ad, CatalogItem, Household, Person
from app.services.rooms import ensure_aliases
from app.services.week import persist_week

# Erie County seed prices. Correct them under Money. Not live ads.
SEED_CATALOG: list[dict] = [
    {
        "key": "chicken_quarters",
        "name": "Chicken leg quarters",
        "default_store": "aldi",
        "unit": "lb",
        "typical_price": 1.49,
        "protein_g": 17.0,
        "kcal": 190.0,
        "staple": True,
    },
    {
        "key": "jasmine_rice",
        "name": "Jasmine rice",
        "default_store": "aldi",
        "unit": "5 lb bag",
        "typical_price": 3.49,
        "protein_g": 30.0,
        "kcal": 7700.0,
        "staple": True,
    },
    {
        "key": "potatoes",
        "name": "Russet potatoes",
        "default_store": "aldi",
        "unit": "5 lb bag",
        "typical_price": 2.99,
        "protein_g": 20.0,
        "kcal": 1750.0,
        "staple": True,
    },
    {
        "key": "eggs",
        "name": "Large eggs",
        "default_store": "aldi",
        "unit": "dozen",
        "typical_price": 2.85,
        "protein_g": 72.0,
        "kcal": 840.0,
        "staple": True,
    },
    {
        "key": "cabbage",
        "name": "Green cabbage",
        "default_store": "aldi",
        "unit": "head",
        "typical_price": 1.49,
        "protein_g": 8.0,
        "kcal": 170.0,
        "staple": True,
    },
    {
        "key": "onions",
        "name": "Yellow onions",
        "default_store": "aldi",
        "unit": "3 lb bag",
        "typical_price": 1.29,
        "protein_g": 6.0,
        "kcal": 250.0,
        "staple": True,
    },
    {
        "key": "carrots",
        "name": "Carrots",
        "default_store": "aldi",
        "unit": "2 lb bag",
        "typical_price": 1.49,
        "protein_g": 4.0,
        "kcal": 320.0,
        "staple": True,
    },
    {
        "key": "butter",
        "name": "Store-brand butter",
        "default_store": "aldi",
        "unit": "lb",
        "typical_price": 3.49,
        "protein_g": 0.0,
        "kcal": 1628.0,
        "staple": True,
    },
    {
        "key": "milk",
        "name": "Whole milk",
        "default_store": "aldi",
        "unit": "gallon",
        "typical_price": 2.79,
        "protein_g": 32.0,
        "kcal": 2400.0,
        "staple": True,
    },
    {
        "key": "beans_canned",
        "name": "Canned beans",
        "default_store": "aldi",
        "unit": "can",
        "typical_price": 0.89,
        "protein_g": 15.0,
        "kcal": 350.0,
        "staple": True,
    },
    {
        "key": "oats",
        "name": "Rolled oats",
        "default_store": "aldi",
        "unit": "42 oz",
        "typical_price": 2.49,
        "protein_g": 50.0,
        "kcal": 1800.0,
        "staple": True,
    },
    {
        "key": "yogurt",
        "name": "Plain yogurt",
        "default_store": "aldi",
        "unit": "32 oz",
        "typical_price": 2.99,
        "protein_g": 40.0,
        "kcal": 560.0,
        "staple": True,
    },
    {
        "key": "frozen_veg",
        "name": "Frozen mixed vegetables",
        "default_store": "aldi",
        "unit": "12 oz",
        "typical_price": 1.15,
        "protein_g": 6.0,
        "kcal": 150.0,
        "staple": True,
    },
    {
        "key": "oil",
        "name": "Vegetable oil",
        "default_store": "aldi",
        "unit": "48 oz",
        "typical_price": 2.99,
        "protein_g": 0.0,
        "kcal": 3840.0,
        "staple": True,
    },
    {
        "key": "bananas",
        "name": "Bananas",
        "default_store": "aldi",
        "unit": "lb",
        "typical_price": 0.49,
        "protein_g": 1.0,
        "kcal": 89.0,
        "staple": False,
    },
    {
        "key": "apples",
        "name": "Apples",
        "default_store": "aldi",
        "unit": "lb",
        "typical_price": 1.29,
        "protein_g": 0.5,
        "kcal": 52.0,
        "staple": False,
    },
    {
        "key": "broth",
        "name": "Chicken broth",
        "default_store": "aldi",
        "unit": "32 oz",
        "typical_price": 1.29,
        "protein_g": 5.0,
        "kcal": 80.0,
        "staple": False,
    },
    {
        "key": "ginger",
        "name": "Fresh ginger",
        "default_store": "walmart",
        "unit": "lb",
        "typical_price": 3.48,
        "protein_g": 2.0,
        "kcal": 80.0,
        "staple": False,
    },
    {
        "key": "quinoa",
        "name": "Quinoa",
        "default_store": "wegmans",
        "unit": "1 lb",
        "typical_price": 4.99,
        "protein_g": 24.0,
        "kcal": 680.0,
        "staple": False,
    },
]


def init_db() -> None:
    get_engine()
    Base.metadata.create_all(bind=get_engine())
    factory = get_session_factory()
    with factory() as session:
        seed_if_empty(session)


def seed_if_empty(session: Session) -> Household:
    household = session.query(Household).first()
    if household is None:
        settings = get_settings()
        household = Household(name="House", weekly_cap=settings.WEEKLY_CAP)
        session.add(household)
        session.flush()
        for alias in ("Oak", "Maple", "Birch"):
            session.add(
                Person(
                    household_id=household.id,
                    legal_name="",
                    alias=alias,
                )
            )
        session.flush()
        for item in SEED_CATALOG:
            session.add(CatalogItem(household_id=household.id, **item))
        session.add(
            Ad(
                household_id=household.id,
                catalog_key="chicken_quarters",
                store="tops",
                price=0.99,
                sale_ends=date(2026, 8, 22),
                source="seed",
            )
        )
        session.flush()
        people = session.query(Person).filter(Person.household_id == household.id).all()
        persist_week(session, household, people, date.today())
    people = session.query(Person).filter(Person.household_id == household.id).all()
    ensure_aliases(session, people)
    session.commit()
    session.refresh(household)
    return household
