from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base, get_engine, get_session_factory, migrate_schema
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
        "default_store": "gfs",
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
        "name": "Vegetable oil (do not buy)",
        "default_store": "aldi",
        "unit": "48 oz",
        "typical_price": 2.99,
        "protein_g": 0.0,
        "kcal": 3840.0,
        "staple": False,
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
    {
        "key": "lamb",
        "name": "Lamb stew meat",
        "default_store": "wegmans",
        "unit": "lb",
        "typical_price": 5.99,
        "protein_g": 25.0,
        "kcal": 250.0,
        "staple": True,
    },
    {
        "key": "flour",
        "name": "Bread flour",
        "default_store": "gfs",
        "unit": "10 lb bag",
        "typical_price": 4.79,
        "protein_g": 120.0,
        "kcal": 16300.0,
        "staple": True,
    },
    {
        "key": "chickpeas_dry",
        "name": "Dry chickpeas",
        "default_store": "gfs",
        "unit": "lb",
        "typical_price": 1.29,
        "protein_g": 19.0,
        "kcal": 364.0,
        "staple": True,
    },
    {
        "key": "lentils",
        "name": "Brown lentils",
        "default_store": "gfs",
        "unit": "lb",
        "typical_price": 1.39,
        "protein_g": 25.0,
        "kcal": 353.0,
        "staple": True,
    },
    {
        "key": "olive_oil",
        "name": "Cold-pressed extra virgin olive oil",
        "default_store": "gfs",
        "unit": "3 L",
        "typical_price": 0.0,
        "protein_g": 0.0,
        "kcal": 3600.0,
        "staple": True,
    },
    {
        "key": "avocado_oil",
        "name": "Cold-pressed avocado oil",
        "default_store": "gfs",
        "unit": "1 L",
        "typical_price": 0.0,
        "protein_g": 0.0,
        "kcal": 1800.0,
        "staple": True,
    },
    {
        "key": "cucumbers",
        "name": "Cucumbers",
        "default_store": "aldi",
        "unit": "lb",
        "typical_price": 0.79,
        "protein_g": 1.0,
        "kcal": 15.0,
        "staple": True,
    },
    {
        "key": "tomatoes",
        "name": "Tomatoes",
        "default_store": "aldi",
        "unit": "lb",
        "typical_price": 1.49,
        "protein_g": 1.0,
        "kcal": 18.0,
        "staple": True,
    },
    {
        "key": "garlic",
        "name": "Garlic",
        "default_store": "aldi",
        "unit": "head",
        "typical_price": 0.79,
        "protein_g": 2.0,
        "kcal": 40.0,
        "staple": True,
    },
    {
        "key": "lemons",
        "name": "Lemons",
        "default_store": "aldi",
        "unit": "2 lb bag",
        "typical_price": 2.89,
        "protein_g": 2.0,
        "kcal": 50.0,
        "staple": True,
    },
]


def init_db() -> None:
    get_engine()
    Base.metadata.create_all(bind=get_engine())
    migrate_schema()
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
    ensure_catalog(session, household)
    people = session.query(Person).filter(Person.household_id == household.id).all()
    ensure_aliases(session, people)
    session.commit()
    session.refresh(household)
    return household


def ensure_catalog(session: Session, household: Household) -> None:
    rows = {
        row.key: row
        for row in session.query(CatalogItem).filter(CatalogItem.household_id == household.id)
    }
    for item in SEED_CATALOG:
        row = rows.get(item["key"])
        if row is None:
            session.add(CatalogItem(household_id=household.id, **item))
            continue
        row.name = item["name"]
        row.default_store = item["default_store"]
        row.unit = item["unit"]
        row.staple = item["staple"]
        if item["key"] in {"olive_oil", "avocado_oil", "oil"}:
            row.typical_price = item["typical_price"]
    session.flush()
