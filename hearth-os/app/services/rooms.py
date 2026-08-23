from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import VaultMessage
from app.services.crypto import decrypt, encrypt, house_scope, private_scope

HOUSE = "house"
PRIVATE = "private"
AGENT_NAMES = ("Kitchen", "Scout", "Budget", "Care")


@dataclass
class RoomMessage:
    id: int
    room: str
    alias: str
    agent_name: Optional[str]
    body: str
    created_at: datetime
    is_agent: bool


def post_house(
    session: Session,
    household_id: int,
    body: str,
    alias: str,
    agent_name: Optional[str] = None,
) -> VaultMessage:
    payload = f"{alias}\n{body}"
    row = VaultMessage(
        household_id=household_id,
        room=HOUSE,
        person_id=None,
        ciphertext=encrypt(house_scope(household_id), payload),
        agent_name=agent_name,
    )
    session.add(row)
    session.flush()
    return row


def post_private(
    session: Session,
    household_id: int,
    person_id: int,
    body: str,
    alias: str,
    agent_name: Optional[str] = None,
) -> VaultMessage:
    payload = f"{alias}\n{body}"
    row = VaultMessage(
        household_id=household_id,
        room=PRIVATE,
        person_id=person_id,
        ciphertext=encrypt(private_scope(household_id, person_id), payload),
        agent_name=agent_name,
    )
    session.add(row)
    session.flush()
    return row


def _decode(row: VaultMessage, scope: str) -> RoomMessage:
    plain = decrypt(scope, row.ciphertext)
    alias, _, body = plain.partition("\n")
    return RoomMessage(
        id=row.id,
        room=row.room,
        alias=alias or ("Agent" if row.agent_name else ""),
        agent_name=row.agent_name,
        body=body,
        created_at=row.created_at,
        is_agent=bool(row.agent_name),
    )


def read_house(session: Session, household_id: int) -> list[RoomMessage]:
    rows = (
        session.query(VaultMessage)
        .filter(VaultMessage.household_id == household_id, VaultMessage.room == HOUSE)
        .order_by(VaultMessage.created_at.asc(), VaultMessage.id.asc())
        .all()
    )
    scope = house_scope(household_id)
    return [_decode(row, scope) for row in rows]


def read_private(session: Session, household_id: int, person_id: int) -> list[RoomMessage]:
    """The only private reader. Callers must not accept a target_person_id from the query string."""
    rows = (
        session.query(VaultMessage)
        .filter(
            VaultMessage.household_id == household_id,
            VaultMessage.room == PRIVATE,
            VaultMessage.person_id == person_id,
        )
        .order_by(VaultMessage.created_at.asc(), VaultMessage.id.asc())
        .all()
    )
    scope = private_scope(household_id, person_id)
    return [_decode(row, scope) for row in rows]


def default_aliases() -> tuple[str, ...]:
    return ("Oak", "Maple", "Birch")


def ensure_aliases(session: Session, people: list) -> None:
    aliases = default_aliases()
    for index, person in enumerate(people):
        if not (person.alias or "").strip():
            person.alias = aliases[index % len(aliases)]
    session.flush()
