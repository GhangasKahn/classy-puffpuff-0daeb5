from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Household, Meal, MealPlan, Person
from app.services.food_law import contains_symptom_word
from app.services.nutrition import cook_verbs
from app.services.shopping import house_has_cancer_track, house_has_soft_food

DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

# Food titles only. No disease names. Jasmine rice + potatoes stay.
# Homemade pita, sourdough, yogurt. Long cold ferment. No organ meats. No Kerrygold.
WEEK_MENU: list[tuple[tuple[str, str], tuple[str, str], tuple[str, str]]] = [
    (
        ("Yogurt, eggs, and oats", "Warm oats in milk. Cook eggs until firm. Plain yogurt on the side. Save a spoon of yogurt to set the next pot."),
        ("Lentils, jasmine rice, cabbage", "Simmer lentils with onion and garlic. Steam rice. Warm cabbage with cold-pressed olive oil or avocado oil and lemon."),
        ("Lamb stew, potatoes, jasmine rice", "Brown lamb. Stew with onion, garlic, carrot, and potato until the meat shreds. Steam rice. Mix bread dough tonight; cold ferment in the fridge 24–48 hours. Bake until dark. Use game only if you already have it."),
    ),
    (
        ("Eggs, potatoes, yogurt", "Pan potatoes. Cook eggs until firm. Yogurt on the side."),
        ("Leftover lamb, rice, cucumber", "Reheat lamb until steaming. Jasmine rice. Slice cucumber, tomato, onion, lemon."),
        ("Roast chicken, potatoes, cabbage", "Roast chicken until fully done. Roast potatoes. Steam cabbage. Shape cold-ferment dough into pita. Bake hot until puffed and browned."),
    ),
    (
        ("Yogurt, oats, apple", "Cook oats in milk. Slice apple. Yogurt."),
        ("Chickpeas in homemade pita", "Warm soaked-and-cooked chickpeas with garlic, lemon, cold-pressed olive oil or avocado oil. Stuff pita. Cucumber on the side. Jasmine rice if you need more plate."),
        ("Chicken, jasmine rice, carrots", "Roast or stew chicken until fully done. Steam rice. Cook carrots. Yogurt on the plate."),
    ),
    (
        ("Eggs, leftover pita, yogurt", "Cook eggs until firm. Toast leftover pita. Yogurt."),
        ("Lentil and potato soup, rice", "Simmer lentils and potato with onion and garlic. Jasmine rice on the side."),
        ("Long-ferment pizza, chicken, tomato", "Stretch cold-ferment dough. Cold-pressed olive oil or avocado oil, tomato, onion, leftover chicken. Hottest oven you have. Bake until the crust is dark. Not boxed pizza dough."),
    ),
    (
        ("Potatoes, eggs, yogurt", "Pan potatoes. Cook eggs until firm. Yogurt."),
        ("Jasmine rice, chickpeas, cabbage", "Warm rice and chickpeas with onion and lemon. Steam cabbage."),
        ("Lamb, jasmine rice, potatoes", "Stew or roast lamb until fully done. Steam rice. Roast potatoes. Cucumber and tomato salad."),
    ),
    (
        ("Oats, milk, yogurt", "Cook oats in milk. Yogurt. Banana if you have it."),
        ("Chicken, pita, cucumber", "Reheat chicken until steaming. Pita. Cucumber, tomato, lemon."),
        ("Chicken, cabbage, potatoes, rice", "Roast chicken until fully done. Potatoes and jasmine rice. Steam cabbage. Bake a sourdough loaf from the cold ferment. Set a new yogurt pot from milk and last yogurt."),
    ),
    (
        ("Eggs and yogurt", "Cook eggs until firm. Plain yogurt."),
        ("Rice, lentils, leftover bread", "Warm jasmine rice and lentils. Slice yesterday's loaf."),
        ("Roast chicken, potatoes, jasmine rice", "Roast chicken until fully done. Roast potatoes. Steam rice. Mix next week's dough; cold ferment. Game stays off the list unless it is already in the house."),
    ),
]


def monday_on_or_before(day: date) -> date:
    return day - timedelta(days=day.weekday())


def build_meals(
    session: Session,
    meal_plan: MealPlan,
    people: list[Person],
    freezer_share: str = "none",
) -> None:
    cancer = house_has_cancer_track(people)
    soft = house_has_soft_food(people)
    extra = cook_verbs(cancer_track=cancer, soft_food=soft)
    extra = (extra + " Fat is cold-pressed olive oil or avocado oil only.").strip()
    if (freezer_share or "none") in {"lamb_half", "beef_half", "elk"}:
        extra += " Use the freezer share. Grocery lamb is off this week's list."
    meal_plan.meals.clear()
    session.flush()
    for day_index, slots in enumerate(WEEK_MENU):
        day_name = DAY_NAMES[day_index]
        for slot, (title, notes) in zip(("breakfast", "lunch", "dinner"), slots):
            cook = notes
            if extra:
                cook = f"{notes} {extra}".strip()
            if contains_symptom_word(title) or contains_symptom_word(cook):
                raise ValueError("meal text must not include diagnosis words")
            session.add(
                Meal(
                    meal_plan_id=meal_plan.id,
                    day_index=day_index,
                    day_name=day_name,
                    slot=slot,
                    title=title,
                    cook_notes=cook,
                    protein_g_est=0.0,
                    kcal_est=0.0,
                )
            )
    session.flush()


def tonight_dinner(meals: list[Meal], today: date, week_start: date) -> Meal | None:
    dinners = [m for m in meals if m.slot == "dinner"]
    if not dinners:
        return None
    offset = (today - week_start).days
    if offset < 0:
        offset = 0
    upcoming = [m for m in dinners if m.day_index >= offset]
    if upcoming:
        return sorted(upcoming, key=lambda m: m.day_index)[0]
    return dinners[0]


def get_or_create_plan(
    session: Session, household: Household, week_start: date
) -> MealPlan:
    plan = (
        session.query(MealPlan)
        .filter(MealPlan.household_id == household.id, MealPlan.week_start == week_start)
        .one_or_none()
    )
    if plan is None:
        plan = MealPlan(household_id=household.id, week_start=week_start, notes="")
        session.add(plan)
        session.flush()
    return plan
