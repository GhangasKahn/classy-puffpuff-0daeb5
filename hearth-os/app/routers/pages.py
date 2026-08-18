from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from app.agents.harness import run_harness
from app.auth import (
    SESSION_AUTH,
    check_pin,
    current_person,
    login_session,
    logout_session,
)
from app.config import get_settings
from app.db import get_session_factory
from app.models import CatalogItem, Household, MealPlan, Person, Recipe, Receipt, ShoppingItem
from app.services.ads import upsert_ad
from app.services.food_law import HOUSE_LAW_REPLY, is_banned
from app.services.meals import monday_on_or_before, tonight_dinner
from app.services.nutrition import person_need
from app.services.rooms import (
    HOUSE,
    PRIVATE,
    post_house,
    post_private,
    read_house,
    read_private,
)
from app.services.scout import fetch_tops_ad_text, parse_optional_date
from app.services.week import persist_week

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _db() -> Session:
    return get_session_factory()()


def _ctx(request: Request, person: Person, extra: Optional[dict] = None) -> dict:
    data = {
        "request": request,
        "person": person,
        "alias": person.alias,
        "version": get_settings().APP_VERSION,
    }
    if extra:
        data.update(extra)
    return data


@router.get("/login")
def login_get(request: Request):
    session = _db()
    try:
        people = session.query(Person).order_by(Person.id.asc()).all()
        return templates.TemplateResponse(
            request,
            "login.html",
            {"people": people, "error": None},
        )
    finally:
        session.close()


@router.post("/login")
def login_post(
    request: Request,
    pin: str = Form(...),
    person_id: int = Form(...),
):
    session = _db()
    try:
        people = session.query(Person).order_by(Person.id.asc()).all()
        person = session.get(Person, person_id)
        if not check_pin(pin) or person is None:
            return templates.TemplateResponse(
                request,
                "login.html",
                {"people": people, "error": "PIN did not match. Try again."},
                status_code=401,
            )
        login_session(request, person.id)
        return RedirectResponse("/", status_code=303)
    finally:
        session.close()


@router.post("/logout")
def logout(request: Request):
    logout_session(request)
    return RedirectResponse("/login", status_code=303)


@router.post("/switch-person")
def switch_person(request: Request, person_id: int = Form(...)):
    if not request.session.get(SESSION_AUTH):
        return RedirectResponse("/login", status_code=303)
    session = _db()
    try:
        person = session.get(Person, person_id)
        if person is None:
            return RedirectResponse("/", status_code=303)
        login_session(request, person.id)
        return RedirectResponse("/", status_code=303)
    finally:
        session.close()


@router.get("/")
def home(request: Request):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        household = session.get(Household, person.household_id)
        people = session.query(Person).filter(Person.household_id == household.id).order_by(Person.id).all()
        week_start = monday_on_or_before(date.today())
        plan = (
            session.query(MealPlan)
            .filter(MealPlan.household_id == household.id, MealPlan.week_start == week_start)
            .one_or_none()
        )
        if plan is None:
            plan = persist_week(session, household, people, date.today(), week_start)
        tonight = tonight_dinner(list(plan.meals), date.today(), week_start)
        total = round(sum(i.qty * i.unit_price for i in plan.items), 2)
        need = person_need(
            weight_kg=person.weight_kg,
            cancer_track=person.cancer_track,
            soft_food=person.soft_food,
            protein_target_g=person.protein_target_g,
            kcal_target=person.kcal_target,
        )
        return templates.TemplateResponse(
            request,
            "home.html",
            _ctx(
                request,
                person,
                {
                    "people": people,
                    "plan": plan,
                    "tonight": tonight,
                    "total": total,
                    "cap": household.weekly_cap,
                    "need": need,
                    "stores": sorted({i.store for i in plan.items}),
                },
            ),
        )
    finally:
        session.close()


@router.post("/flags")
def update_flags(
    request: Request,
    energy_first: Optional[str] = Form(None),
    soft_food: Optional[str] = Form(None),
    weight_kg: Optional[str] = Form(None),
):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        person.cancer_track = energy_first == "on"
        person.soft_food = soft_food == "on"
        if weight_kg and weight_kg.strip():
            try:
                person.weight_kg = float(weight_kg)
            except ValueError:
                pass
        else:
            person.weight_kg = None
        session.commit()
        household = session.get(Household, person.household_id)
        people = session.query(Person).filter(Person.household_id == household.id).all()
        persist_week(session, household, people, date.today())
        return RedirectResponse("/", status_code=303)
    finally:
        session.close()


@router.get("/rooms")
def rooms_get(request: Request, room: str = "house"):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        if room != PRIVATE:
            room = HOUSE
        if room == PRIVATE and not person:
            room = HOUSE
        if room == PRIVATE:
            messages = read_private(session, person.household_id, person.id)
        else:
            messages = read_house(session, person.household_id)
        return templates.TemplateResponse(
            request,
            "rooms.html",
            _ctx(request, person, {"room": room, "messages": messages, "error": None}),
        )
    finally:
        session.close()


@router.post("/rooms")
def rooms_post(
    request: Request,
    body: str = Form(""),
    room: str = Form("house"),
):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        if room != PRIVATE:
            room = HOUSE
        text = (body or "").strip()
        if not text:
            return RedirectResponse(f"/rooms?room={room}", status_code=303)
        if room == PRIVATE:
            post_private(session, person.household_id, person.id, text, person.alias)
        else:
            post_house(session, person.household_id, text, person.alias)
        reply = run_harness(session, person, text, room)
        agent = "Care" if room == PRIVATE else "Kitchen"
        lower = text.lower()
        if any(w in lower for w in ("price", "ad", "tops", "circular")):
            agent = "Scout"
        elif any(w in lower for w in ("cap", "budget", "dollar")):
            agent = "Budget"
        if room == PRIVATE:
            post_private(session, person.household_id, person.id, reply, agent, agent_name=agent)
        else:
            post_house(session, person.household_id, reply, agent, agent_name=agent)
        session.commit()
        return RedirectResponse(f"/rooms?room={room}", status_code=303)
    finally:
        session.close()


@router.get("/shop")
def shop(request: Request):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        household = session.get(Household, person.household_id)
        week_start = monday_on_or_before(date.today())
        plan = (
            session.query(MealPlan)
            .filter(MealPlan.household_id == household.id, MealPlan.week_start == week_start)
            .one_or_none()
        )
        grouped: dict[str, list[ShoppingItem]] = {}
        totals: dict[str, float] = {}
        grand = 0.0
        if plan:
            for item in plan.items:
                grouped.setdefault(item.store, []).append(item)
                totals[item.store] = totals.get(item.store, 0.0) + item.qty * item.unit_price
                grand += item.qty * item.unit_price
        protein = 0.0
        if plan:
            catalog = {
                c.key: c
                for c in session.query(CatalogItem).filter(CatalogItem.household_id == household.id)
            }
            for item in plan.items:
                cat = catalog.get(item.catalog_key)
                if cat:
                    protein += cat.protein_g * item.qty
        return templates.TemplateResponse(
            request,
            "shop.html",
            _ctx(
                request,
                person,
                {
                    "grouped": grouped,
                    "totals": {k: round(v, 2) for k, v in totals.items()},
                    "grand": round(grand, 2),
                    "cap": household.weekly_cap,
                    "protein": round(protein, 1),
                    "week_start": week_start,
                },
            ),
        )
    finally:
        session.close()


@router.post("/shop/check")
def shop_check(request: Request, item_id: int = Form(...)):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        item = session.get(ShoppingItem, item_id)
        if item is not None:
            plan = session.get(MealPlan, item.meal_plan_id)
            if plan and plan.household_id == person.household_id:
                item.checked = not item.checked
                session.commit()
        return RedirectResponse("/shop", status_code=303)
    finally:
        session.close()


@router.post("/week/rebuild")
def rebuild_week(request: Request):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        household = session.get(Household, person.household_id)
        people = session.query(Person).filter(Person.household_id == household.id).all()
        persist_week(session, household, people, date.today())
        return RedirectResponse("/shop", status_code=303)
    finally:
        session.close()


@router.get("/cook")
def cook(request: Request):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        household = session.get(Household, person.household_id)
        week_start = monday_on_or_before(date.today())
        plan = (
            session.query(MealPlan)
            .filter(MealPlan.household_id == household.id, MealPlan.week_start == week_start)
            .one_or_none()
        )
        days: dict[int, dict] = {}
        if plan:
            for meal in sorted(plan.meals, key=lambda m: (m.day_index, m.slot)):
                days.setdefault(
                    meal.day_index, {"name": meal.day_name, "meals": []}
                )
                days[meal.day_index]["meals"].append(meal)
        return templates.TemplateResponse(
            request,
            "cook.html",
            _ctx(request, person, {"days": days, "week_start": week_start}),
        )
    finally:
        session.close()


@router.get("/money")
def money_get(request: Request):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        household = session.get(Household, person.household_id)
        catalog = (
            session.query(CatalogItem)
            .filter(CatalogItem.household_id == household.id)
            .order_by(CatalogItem.name)
            .all()
        )
        receipts = (
            session.query(Receipt)
            .filter(Receipt.household_id == household.id)
            .order_by(Receipt.purchased_at.desc(), Receipt.id.desc())
            .limit(20)
            .all()
        )
        return templates.TemplateResponse(
            request,
            "money.html",
            _ctx(
                request,
                person,
                {"catalog": catalog, "receipts": receipts, "notice": None},
            ),
        )
    finally:
        session.close()


@router.post("/money/ad")
def money_ad(
    request: Request,
    catalog_key: str = Form(...),
    store: str = Form(...),
    price: float = Form(...),
    sale_ends: str = Form(""),
):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        upsert_ad(
            session,
            person.household_id,
            catalog_key,
            store.strip().lower(),
            float(price),
            parse_optional_date(sale_ends),
            source="manual",
        )
        household = session.get(Household, person.household_id)
        people = session.query(Person).filter(Person.household_id == household.id).all()
        persist_week(session, household, people, date.today())
        return RedirectResponse("/money", status_code=303)
    finally:
        session.close()


@router.post("/money/receipt")
def money_receipt(
    request: Request,
    store: str = Form(...),
    amount: float = Form(...),
    purchased_at: str = Form(...),
    notes: str = Form(""),
):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        session.add(
            Receipt(
                household_id=person.household_id,
                store=store.strip().lower(),
                amount=float(amount),
                purchased_at=parse_optional_date(purchased_at) or date.today(),
                notes=(notes or "")[:200],
            )
        )
        session.commit()
        return RedirectResponse("/money", status_code=303)
    finally:
        session.close()


@router.post("/money/scout")
def money_scout(request: Request):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        fetch_tops_ad_text(session)
        return RedirectResponse("/money", status_code=303)
    finally:
        session.close()


@router.get("/recipes")
def recipes_get(request: Request):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        recipes = (
            session.query(Recipe)
            .filter(Recipe.household_id == person.household_id)
            .order_by(Recipe.created_at.desc())
            .all()
        )
        return templates.TemplateResponse(
            request,
            "recipes.html",
            _ctx(request, person, {"recipes": recipes, "notice": None}),
        )
    finally:
        session.close()


@router.post("/recipes")
def recipes_post(
    request: Request,
    title: str = Form(""),
    body: str = Form(""),
    room: str = Form("house"),
    upload: Optional[UploadFile] = File(None),
):
    session = _db()
    try:
        person = current_person(request, session)
        if person is None:
            return RedirectResponse("/login", status_code=303)
        text = body or ""
        if upload and upload.filename:
            raw = upload.file.read()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("latin-1", errors="replace")
        banned, _reason = is_banned(text + " " + title)
        if banned:
            recipes = (
                session.query(Recipe)
                .filter(Recipe.household_id == person.household_id)
                .all()
            )
            return templates.TemplateResponse(
                request,
                "recipes.html",
                _ctx(
                    request,
                    person,
                    {"recipes": recipes, "notice": f"Kitchen: {HOUSE_LAW_REPLY}"},
                ),
            )
        if room == PRIVATE:
            post_private(
                session,
                person.household_id,
                person.id,
                text or title,
                person.alias,
            )
            session.commit()
            return RedirectResponse("/rooms?room=private", status_code=303)
        heading = (title or text.strip().splitlines()[0] if text.strip() else "House recipe")[:80]
        session.add(
            Recipe(
                household_id=person.household_id,
                title=heading or "House recipe",
                body=text,
            )
        )
        session.commit()
        return RedirectResponse("/recipes", status_code=303)
    finally:
        session.close()
