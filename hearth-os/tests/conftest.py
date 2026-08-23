from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import clear_settings_cache
from app.db import reset_engine


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    db_file = tmp_path / "data" / "hearth.db"
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-stable-value")
    monkeypatch.setenv("HOUSEHOLD_PIN", "4829")
    monkeypatch.setenv("HOUSEHOLD_ENC_KEY", "")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("XAI_API_KEY", "")
    monkeypatch.setenv("CRON_TOKEN", "cron-test-token")
    monkeypatch.setenv("APP_VERSION", "test")
    clear_settings_cache()
    reset_engine()
    yield db_file
    reset_engine()
    clear_settings_cache()


@pytest.fixture
def db_session(db_env):
    from app.seed import init_db
    from app.db import get_session_factory

    init_db()
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_env):
    from app.main import create_app

    application = create_app()
    with TestClient(application) as test_client:
        yield test_client


@pytest.fixture
def logged_in(client, db_session):
    from app.models import Person

    person = db_session.query(Person).order_by(Person.id.asc()).first()
    response = client.post(
        "/login",
        data={"pin": "4829", "person_id": str(person.id)},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return person
