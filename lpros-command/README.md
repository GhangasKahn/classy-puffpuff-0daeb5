# LPROS COMMAND

Open-source **ZIK Analytics + AutoDS** alternative — built for profitable dropshipping lethality, not listing spam.

| Them | Us |
|------|----|
| ZIK: sold/revenue proxies, SaaS | Fee-true net, scam kills, perceived-value rank, category crawl |
| AutoDS: auto-list + auto-order | Control plane that HOLDs weak margin; AutoDS/DSers optional executors |
| Locked cloud | Local Hermes-style swarm + official eBay APIs |

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
- **Brain** — GO / CAUTION / NO-GO brief  
- **Fulfillment gate** — AUTO vs HOLD (AutoDS as executor, not brain)  
- **Conditioning** — sale/return outcomes nudge psych weights  

Browser playbooks (Terapeak assist): `src/browser/playbooks.md` or `/api/playbook`.

## API

| Endpoint | Role |
|----------|------|
| `POST /api/swarm` | Full research swarm (+ optional `evidence`) |
| `POST /api/intel` | Competitor landscape |
| `POST /api/evidence/verify` | Harden one candidate to PASS/FAIL |
| `POST /api/listing/draft` | Title/bullets/specifics shell |
| `GET/POST /api/outcomes` | Conditioning log |
| `POST /api/econ` / `forecast` | Fee-true cash math |
| `POST /api/fulfill/decide` | HOLD vs AUTO |

## Stack (open)

Node 20 · eBay Browse/Taxonomy · LPROS core · optional Ollama/Hermes later · Cursor Browser for Terapeak only when needed.
