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
```

## Architecture

- **Scout** — LPROS pipeline rank  
- **Intel** — competitor density, price ladder, seller HHI (ZIK-class)  
- **Crawler** — optional full category pagination  
- **Economics** — listings-needed / stress triad  
- **Quality** — merge lethal board (anti-scam)  
- **Brain** — GO / CAUTION / NO-GO brief  
- **Fulfillment gate** — AUTO vs HOLD (AutoDS as executor, not brain)

Browser playbooks (Terapeak assist): `src/browser/playbooks.md` or `/api/playbook`.

## Stack (open)

Node 20 · eBay Browse/Taxonomy · LPROS core · optional Ollama/Hermes later · Cursor Browser for Terapeak only when needed.
