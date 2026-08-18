from __future__ import annotations

import json
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.agents.prompts import HOUSE_FALLBACK, HOUSE_SYSTEM, PRIVATE_FALLBACK, PRIVATE_SYSTEM
from app.agents.tools import TOOL_SPECS, dispatch_tool, maybe_store_house_recipe, tool_build_week
from app.config import get_settings
from app.models import Person
from app.services.food_law import HOUSE_LAW_REPLY, is_banned
from app.services.quiet import infer_quiet_adds, record_quiet_needs
from app.services.meals import monday_on_or_before
from app.services.week import persist_week
from datetime import date

MAX_TOOL_LOOPS = 8


def _agent_for(text: str) -> str:
    lower = (text or "").lower()
    if any(w in lower for w in ("price", "ad", "tops", "circular", "scout")):
        return "Scout"
    if any(w in lower for w in ("cap", "budget", "dollar", "receipt")):
        return "Budget"
    if any(w in lower for w in ("quiet", "soft", "flu", "headache", "stomach", "care")):
        return "Care"
    return "Kitchen"


def deterministic_handle(
    session: Session,
    person: Person,
    text: str,
    room: str,
) -> str:
    banned, _reason = is_banned(text)
    if banned:
        return HOUSE_LAW_REPLY

    lower = (text or "").lower()
    if room == "house":
        recipe_reply = maybe_store_house_recipe(session, person.household_id, text, room)
        if recipe_reply:
            return recipe_reply
        if "recipe" in lower or len(text) > 400:
            maybe_store_house_recipe(session, person.household_id, text, "house")

    if room == "private":
        adds = infer_quiet_adds(text)
        if adds:
            week_start = monday_on_or_before(date.today())
            ack = record_quiet_needs(session, person.household_id, week_start, person.id, adds)
            from app.models import Household

            household = session.get(Household, person.household_id)
            people = session.query(Person).filter(Person.household_id == person.household_id).all()
            persist_week(session, household, people, date.today(), week_start)
            return ack or PRIVATE_FALLBACK

    if any(w in lower for w in ("build", "week", "plan", "shop", "cook")):
        tool_build_week(session)
        return HOUSE_FALLBACK

    if room == "private":
        return PRIVATE_FALLBACK
    return HOUSE_FALLBACK


def _chat_completion(messages: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    response = httpx.post(
        settings.XAI_API_URL,
        headers={
            "Authorization": f"Bearer {settings.XAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.XAI_MODEL,
            "messages": messages,
            "tools": TOOL_SPECS,
            "tool_choice": "auto",
        },
        timeout=45.0,
    )
    response.raise_for_status()
    return response.json()


def run_harness(
    session: Session,
    person: Person,
    text: str,
    room: str,
) -> str:
    settings = get_settings()
    if not settings.grok_configured():
        return deterministic_handle(session, person, text, room)

    system = PRIVATE_SYSTEM if room == "private" else HOUSE_SYSTEM
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]
    try:
        for _ in range(MAX_TOOL_LOOPS):
            data = _chat_completion(messages)
            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                content = (message.get("content") or "").strip()
                return content or deterministic_handle(session, person, text, room)
            messages.append(message)
            for call in tool_calls:
                fn = call.get("function") or {}
                name = fn.get("name") or ""
                raw_args = fn.get("arguments") or "{}"
                try:
                    arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    arguments = {}
                result = dispatch_tool(
                    session, name, arguments, room=room, person_id=person.id
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id", name),
                        "content": json.dumps(result),
                    }
                )
        return deterministic_handle(session, person, text, room)
    except httpx.HTTPError:
        return deterministic_handle(session, person, text, room)
