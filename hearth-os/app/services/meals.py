from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Household, Meal, MealPlan, Person
from app.services.food_law import contains_symptom_word
from app.services.nutrition import cook_verbs
from app.services.shopping import house_has_cancer_track, house_has_soft_food

DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

# Food titles only. No disease names. Jasmine rice + potatoes every day.
WEEK_MENU: list[tuple[tuple[str, str], tuple[str, str], tuple[str, str]]] = [
    (
        ("Oatmeal and eggs", "Cook oats in milk. Cook eggs until firm."),
        ("Jasmine rice, beans, and cabbage", "Warm rice and beans. Steam cabbage."),
        ("Roast chicken, potatoes, jasmine rice", "Roast chicken. Roast potatoes. Steam rice."),
    ),
    (
        ("Eggs and potatoes", "Cook eggs until firm. Pan potatoes."),
        ("Chicken and jasmine rice", "Reheat chicken with rice."),
        ("Chicken, cabbage, potatoes", "Simmer chicken. Boil potatoes. Steam cabbage."),
    ),
    (
        ("Yogurt, oats, and banana", "Stir oats into yogurt. Slice banana."),
        ("Bean and potato plate", "Warm beans. Boil potatoes."),
        ("Chicken quarters, jasmine rice, carrots", "Roast chicken. Steam rice. Cook carrots."),
    ),
    (
        ("Eggs, oats, and apples", "Cook eggs until firm. Cook oats. Slice apple."),
        ("Rice and leftover chicken", "Reheat fully. Serve with jasmine rice."),
        ("Chicken, potatoes, frozen vegetables", "Roast chicken. Roast potatoes. Heat vegetables."),
    ),
    (
        ("Potatoes and eggs", "Pan potatoes. Cook eggs until firm."),
        ("Jasmine rice and beans", "Warm rice and beans with onion."),
        ("Chicken, cabbage, jasmine rice", "Roast chicken. Steam cabbage and rice."),
    ),
    (
        ("Oatmeal, milk, and banana", "Cook oats in milk. Slice banana."),
        ("Chicken potato bowl", "Reheat chicken. Boil potatoes."),
        ("Roast chicken, potatoes, carrots", "Roast chicken and potatoes. Cook carrots."),
    ),
    (
        ("Eggs and yogurt", "Cook eggs until firm. Plain yogurt on the side."),
        ("Jasmine rice, beans, cabbage", "Warm rice and beans. Steam cabbage."),
        ("Chicken, jasmine rice, potatoes", "Roast chicken. Steam rice. Roast potatoes."),
    ),
]


def monday_on_or_before(day: date) -> date:
    return day - timedelta(days=day.weekday())


def build_meals(
    session: Session,
    meal_plan: MealPlan,
    people: list[Person],
) -> None:
    cancer = house_has_cancer_track(people)
    soft = house_has_soft_food(people)
    extra = cook_verbs(cancer_track=cancer, soft_food=soft)
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
