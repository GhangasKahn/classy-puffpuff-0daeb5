from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.db import get_session_factory
from app.models import Person
from app.routers import health, internal, pages
from app.seed import init_db
from app.services.rooms import ensure_aliases


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.refuse_insecure_prod()
    init_db()
    session = get_session_factory()()
    try:
        people = session.query(Person).all()
        ensure_aliases(session, people)
        session.commit()
    finally:
        session.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="Hearth OS", lifespan=lifespan, docs_url=None, redoc_url=None)
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        session_cookie="hearth_session",
        same_site="lax",
        https_only=settings.ENV == "prod",
    )
    static_dir = Path(__file__).resolve().parent / "static"
    application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    application.include_router(health.router)
    application.include_router(internal.router)
    application.include_router(pages.router)

    @application.get("/chat")
    def chat_compat(request: Request, room: str = "house"):
        person_authed = bool(request.session.get("authed") and request.session.get("person_id"))
        if room == "private" and not person_authed:
            return RedirectResponse("/rooms?room=house", status_code=303)
        target = "private" if room == "private" and person_authed else "house"
        return RedirectResponse(f"/rooms?room={target}", status_code=303)

    return application


app = create_app()
