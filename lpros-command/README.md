# LPROS COMMAND

Open-source **ZIK Analytics + AutoDS** alternative — built for profitable dropshipping lethality, not listing spam.

| Them | Us |
|------|----|
| ZIK: sold/revenue proxies, SaaS | Fee-true net, scam kills, perceived-value rank, category crawl |
| AutoDS: auto-list + auto-order | Control plane that HOLDs weak margin; AutoDS/DSers optional executors |
| Locked cloud | Local Hermes-style swarm + official eBay APIs |

## Real-world daily loop (usable today)

1. **Research** — swarm finds high-PV SKUs (Browse API)
2. **Evidence** — paste Terapeak sold count + 2 supplier quotes → PASS
3. **Promote** — save PASS rows into local SKU registry
4. **Export** — CSV/JSON for Seller Hub (works without Sell OAuth)
5. **Publish** — dry-run Inventory payload; live when `EBAY_USER_REFRESH_TOKEN` + policies set
6. **Orders** — ingest sale → HOLD/AUTO gate → attach tracking → dry-run push

```bash
cd lpros-command
EBAY_ENV=production npm start          # http://127.0.0.1:8790

# CLI ops
npm run ops -- promote --title "Solid oak desk organizer" --price 49 --sold 28 --cost 18 --alt-cost 19.5
npm run ops -- export
npm run ops -- dry-run --sku <SKU>
npm run ops -- ingest --sku <SKU> --total 49 --cost 18
npm run ops -- auth
```

Without a user refresh token you still run a real business from the desk: research → evidence → registry → CSV into Seller Hub → order ingest → HOLD until tracking exists.

## Netlify deploy

Live path after deploy: **`/lpros-command/`** (also `/lpros`).

API: `/lpros-command/api/*` → Netlify Function `lpros-api` (26s timeout).

1. Push this repo to the linked Netlify site (or `npx netlify deploy --prod`).
2. In Netlify → Site settings → Environment variables, set at least:
   - `EBAY_ENV=production`
   - `EBAY_PRD_APP_ID` / `EBAY_PRD_CERT_ID` (and Dev ID)
3. Redeploy. Open `https://<site>.netlify.app/lpros-command/`

Notes: SKU/order JSON on Netlify is **ephemeral** (`/tmp`). For durable registry use local `npm start` or add a DB later. See `netlify-env.example`.

## Start desk

```bash
# needs ebay-sold-items/.env (EBAY_ENV=production)
cd lpros-command
npm start
# → http://127.0.0.1:8790
```

## CLI swarm

```bash
npm run swarm -- --q "solid wood desk organizer" --category-id 25339 --min-price 35
npm run swarm -- --q "cable management tray" --category-id 25339 --deep
# Harden CONDITIONAL → PASS with Terapeak + dual quotes:
npm run swarm -- --q "solid wood desk organizer" --category-id 25339 --sold 28 --cost 18 --alt-cost 19.5
```

## Architecture

- **Scout** — LPROS pipeline rank (parallel with Intel)  
- **Intel** — competitor density, price ladder, seller HHI (ZIK-class)  
- **Crawler** — optional full category pagination  
- **Economics** — listings-needed / stress triad  
- **Quality** — merge lethal board (anti-scam)  
- **Evidence** — Terapeak sold + dual supplier costs → PASS  
- **Copy** — deterministic listing drafts  
- **Registry / Export** — durable SKUs + Seller Hub CSV  
- **Publish** — Inventory API dry-run / live  
- **Orders** — ingest + HOLD/AUTO + tracking push dry-run  
- **Brain** — GO / CAUTION / NO-GO brief  
- **Conditioning** — sale/return outcomes nudge psych weights  

Browser playbooks (Terapeak assist): `src/browser/playbooks.md` or `/api/playbook`.

## API

| Endpoint | Role |
|----------|------|
| `POST /api/swarm` | Full research swarm (+ optional `evidence`, `promotePass`) |
| `POST /api/skus/promote` | Save candidate into registry |
| `GET /api/skus` | List registry |
| `POST /api/export` | Write CSV/JSON under `data/exports/` |
| `GET /api/export/csv` | Download ready CSV |
| `POST /api/publish` | Dry-run (default) or `{ live:true }` Inventory publish |
| `POST /api/orders/ingest` | Import sale + fulfill gate |
| `POST /api/orders/tracking` | Attach carrier tracking |
| `POST /api/evidence/verify` | Harden one candidate to PASS/FAIL |
| `GET /api/auth/status` | App vs user-token capability |

## Live Sell publish (optional)

Add to `ebay-sold-items/.env`:

- `EBAY_USER_REFRESH_TOKEN`
- `EBAY_FULFILLMENT_POLICY_ID` / `PAYMENT` / `RETURN`
- `EBAY_MERCHANT_LOCATION_KEY`

Until then, mode stays `export_and_dry_run` — still production-usable via Seller Hub CSV.

## Stack (open)

Node 20 · eBay Browse/Taxonomy · Sell Inventory/Fulfillment (optional user token) · LPROS core · Cursor Browser for Terapeak when Insights gated.
