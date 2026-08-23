from app.config import Settings, clear_settings_cache


def test_health_shape_dev(client):
    payload = client.get("/health").json()
    assert set(payload) == {"ok", "db", "grok", "version"}
    assert payload["ok"] is True
    assert payload["db"] is True
    assert payload["grok"] is False
    assert payload["version"]


def test_prod_refuses_default_secrets(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("SECRET_KEY", "please-change-me-now")
    monkeypatch.setenv("HOUSEHOLD_PIN", "4829")
    clear_settings_cache()
    settings = Settings()
    try:
        raised = False
        try:
            settings.refuse_insecure_prod()
        except RuntimeError:
            raised = True
        assert raised
    finally:
        clear_settings_cache()
