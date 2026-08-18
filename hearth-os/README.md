# Hearth OS

Household operating system for three adults in Erie County, NY.

**This is not the orange BEDROCK website.** Hearth is this folder. It runs on a computer in the house, not on Netlify. A public sign for it is `/hearth/` on the site. The GitHub map is in the root `README.md`.

Not a recipe blog. It is the shopper, cook, and budgeter: weekly ads, store-split lists, protein math, and a Grok agent harness you message in the app.

## Privacy

- House room: aliases only. Agents are named (Kitchen, Scout, Budget, Care).
- Private room: one member + agents. Encrypted at rest. Other members cannot open it.
- Stomach flu / headache in private can add bananas, broth, ginger to the list with no name and no diagnosis.
- This is not Signal. Agents must read private notes to shop. The house cannot.

## What it does

- **Scout** stores Erie County prices (Tops / Aldi / Walmart / Wegmans). Seed prices ship with the app. You correct a price in one form. Optional live fetch of the Tops circular.
- **Kitchen** builds a 7-day cook sheet. Jasmine rice + potatoes. Soft-food variants if someone needs them.
- **Budget** splits the cart by store against a weekly cap.
- **Care** enforces house law: no organs, no Kerrygold, no keto, cancer calories first.
- **Harness** is Grok (`XAI_API_KEY`) with tools. If the key is missing, the deterministic engines still build the week.

## Run locally

```bash
cd hearth-os
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit HOUSEHOLD_PIN and SECRET_KEY
make test
make run
```

Open `http://127.0.0.1:8080`. Default PIN is `4829`. Change it.

Phones: add to home screen (PWA). Same PIN for mom and dad. Switch person on Home.

## Production

1. Set `HOUSEHOLD_PIN`, `SECRET_KEY`, and `XAI_API_KEY` in `.env`.
2. Set `ENV=prod`. Prod will refuse to boot if `SECRET_KEY` contains `change-me` or the PIN is still `4829`.
3. Put it on a LAN or Tailscale box. Do not expose it to the open internet without TLS and a real identity layer.
4. `mkdir -p data && sudo chown 10001:10001 data`
5. `docker compose up --build -d`
6. Health: `GET /health`

`docker-compose.yml` binds `127.0.0.1:8080` by default. To serve on a tailnet IP, comment that mapping and bind the Tailscale address instead. Do not publish `0.0.0.0` to the public internet.

SQLite + WAL is the correct database for one household. Do not add Postgres until you have more than one house.

### Backup and restore

```bash
# backup
cp data/hearth.db data/hearth-backup-$(date +%F).db

# restore (stop the app first)
cp data/hearth-backup-YYYY-MM-DD.db data/hearth.db
```

Copy `hearth.db` only. WAL/SHM files can be omitted if the app is stopped first.

### Sunday Scout (optional)

Set `CRON_TOKEN` in `.env`. Then:

```bash
curl -sS -X POST http://127.0.0.1:8080/internal/scout \
  -H "X-Cron-Token: $CRON_TOKEN"
```

That fetch is best-effort raw HTML stored in `AdFetch`. Seed + the Money form remain the source of truth.

## Agent contract

Grok tools:

- `get_household_state`
- `get_current_ads`
- `fetch_tops_circular`
- `upsert_ad`
- `build_week`
- `apply_quiet_from_private_text` (private room only)

You can also paste a recipe or upload a `.txt`. House path stores a Recipe. Private paste stays a vault message. Kitchen refuses Kerrygold, organs, and keto.

## Weekly loop

1. Sunday: open Rooms. “Build this week. Use Tops chicken if it is still $0.99.”
2. Shop the store-split list. Check items off.
3. Log the receipt under Money.
4. If someone cannot eat dinner, say so in the private room. Do not cut the calories/protein plate.

## Limits (on purpose)

- Weekly-ad HTML is hostile. Scout does not pretend it has a perfect scrape. Seed + manual correction is the source of truth.
- Coupons: Tops circular price is the coupon. The app will not add junk to “save” fifty cents.
- This is not medical advice. It is a kitchen control system.
- Seed chicken: $0.99 at Tops through 2026-08-22. After that, the seed does not assume a live chicken sale.
