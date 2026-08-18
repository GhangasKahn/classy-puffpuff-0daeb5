# Hearth OS — baseline audit

This workspace did not contain a prior `hearth-os/` tree (`/home/workdir/artifacts/hearth-os` was not present). The app was implemented against `ENGINEERING_REPORT.md` as a FastAPI + SQLite + Jinja household kitchen, then audited.

## File map

```
hearth-os/
  app/main.py                 FastAPI app, session cookie, /chat → /rooms
  app/config.py               ENV, secrets, optional HOUSEHOLD_ENC_KEY
  app/db.py                   SQLite + WAL + foreign keys, writable check
  app/models.py               Household, Person, ads, meals, vault, recipes
  app/auth.py                 PIN + person session
  app/seed.py                 Three aliases, Erie County catalog, chicken sale ad
  app/routers/pages.py        Home, Rooms, Shop, Cook, Money, Recipes
  app/routers/health.py       GET /health {ok, db, grok, version}
  app/routers/internal.py     POST /internal/scout (CRON_TOKEN)
  app/services/food_law.py    No keto / organs / Kerrygold
  app/services/crypto.py      Fernet per room scope
  app/services/rooms.py       House (no person_id) / private reader
  app/services/nutrition.py   Estimate floors; 70 kg placeholder
  app/services/ads.py         Ad table first; chicken sale window
  app/services/scout.py       Best-effort Tops fetch → AdFetch
  app/services/shopping.py    Store split, jasmine rice staple
  app/services/quiet.py       Keyword extras, food names only
  app/services/meals.py       7-day sheet, tonight = upcoming dinner
  app/services/week.py        persist_week copies quiet needs
  app/agents/harness.py       Grok tools, httpx → deterministic fallback
  app/agents/tools.py         Six tools; quiet is private-only
  app/templates/              Timber-dark Jinja (Starlette request-first)
  app/static/                 CSS, PWA, CSS/JS service worker
  tests/                      Isolated tmp sqlite, no live network
```

## What works

- PIN login, alias-only person switcher
- House vs private rooms; private Fernet scope isolation
- Quiet needs: private “stomach flu” adds bananas/broth/ginger with no name and no diagnosis on the list
- Week plan: jasmine rice + potatoes, Tops chicken while the $0.99 ad is live through 2026-08-22
- Deterministic engines when `XAI_API_KEY` is absent
- Health JSON with a real sqlite write+read
- Prod boot refuses default PIN / `change-me` secrets

## What is stubbed / leftover

- Tops circular: raw `AdFetch` excerpt only. Not a price parser.
- Grok tool loop: implemented; not live-verified in this environment (no API key).
- Crypto is server-mediated encryption at rest, not Signal E2E.
- One household PIN, no per-device identity.
- CSRF token not added (same-origin cookie residual).

## Threat model leftovers

- Shared tablet + same PIN can open whoever’s private room after a person switch.
- Stale seed prices if nobody corrects them under Money.
- Box on the open internet is out of scope; compose binds 127.0.0.1.

## Commands

```bash
cd hearth-os
PYTHONPATH=. python3 -m pytest -q
PYTHONPATH=. python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Health: `GET /health`

## pytest

```
...........................                                              [100%]
27 passed in 1.11s
```
