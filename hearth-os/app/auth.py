from __future__ import annotations

import hmac
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.config import get_settings
from app.models import Person


SESSION_AUTH = "authed"
SESSION_PERSON = "person_id"


def check_pin(pin: str) -> bool:
    expected = get_settings().HOUSEHOLD_PIN.encode("utf-8")
    got = (pin or "").encode("utf-8")
    if len(got) != len(expected):
        return hmac.compare_digest(expected, expected) and False
    return hmac.compare_digest(got, expected)


def current_person(request: Request, session: Session) -> Optional[Person]:
    if not request.session.get(SESSION_AUTH):
        return None
    person_id = request.session.get(SESSION_PERSON)
    if not person_id:
        return None
    return session.get(Person, int(person_id))


def require_person(request: Request, session: Session) -> Person | RedirectResponse:
    person = current_person(request, session)
    if person is None:
        return RedirectResponse("/login", status_code=303)
    return person


def login_session(request: Request, person_id: int) -> None:
    request.session[SESSION_AUTH] = True
    request.session[SESSION_PERSON] = person_id


def logout_session(request: Request) -> None:
    request.session.clear()
