# eBay Sold Items — BEDROCK comps bridge

Node service that talks to the **eBay Developer Program** keyset named `sold items` and serves vault comps for BEDROCK’s LIVE / Ledger UI.

## What it does

| Route | Purpose |
|-------|---------|
| `GET /health` | Env + configured flag |
| `GET /v1/ebay/token-check` | Client-credentials OAuth smoke |
| `GET /v1/ebay/search?q=` | Browse API — **active** listings |
| `GET /v1/ebay/sold?q=` | Marketplace Insights — **sold** (~90d), if entitled |
| `GET /v1/market/alt/comps?category=&ref=` | BEDROCK contract used by Vault / LIVE |

### Sold vs active (important)

- **Finding API / findCompletedItems** is decommissioned.
- **Marketplace Insights** is the official sold-history API (limited release). If your keyset is not entitled, `/v1/ebay/sold` returns `listings-needed` and `/v1/market/alt/comps` falls back to **Browse** asking prices with `evidenceStatus: "partial"`.
- This matches LPROS **listings-needed** discipline: never treat asking prices as sold comps silently.

## Setup

1. Create keys at [eBay Application Keys](https://developer.ebay.com/my/keys) (Sandbox + Production).
2. Copy env template and fill IDs (never commit Cert ID):

```bash
cd ebay-sold-items
cp .env.example .env
# edit .env — EBAY_ENV=sandbox for testing
```

3. Run:

```bash
npm start
# → http://127.0.0.1:8787
```

4. In BEDROCK **CONFIG**, set cloud URL to `http://127.0.0.1:8787` (default), then use LIVE → **FETCH COMPS**.

### Smoke

```bash
npm test
npm run smoke   # live OAuth + comps (needs .env)
```

## Security

- Cert ID is a **client secret**. Keep it in `.env` only (gitignored).
- If a Cert ID was shown in a screenshot or chat, **Rotate (Reset) Cert ID** in the eBay portal for both Sandbox and Production, then update `.env`.
- Browser clients must never embed App Secret; this service is the proxy.

## LPROS

See `lpros_advanced/.cursor/skills/ebay-listings/SKILL.md` for agent procedure when attaching eBay evidence to forecasts.
