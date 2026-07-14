# BEDROCK — Deploy and Activate

Runbook for bringing the Phase 0+1 backend online and pointing the PWA at it.
Nothing here changes your existing local vault until the client ONLINE panel is wired.

## Prerequisites

- Cloudflare account
- Node 20+
- The domain (or preview URL) that will serve `site/`

## 1. Backend

```bash
cd backend
npm install
npx wrangler login

npx wrangler d1 create bedrock
npx wrangler kv namespace create SESS
```

Paste both IDs into `wrangler.toml` (`database_id` and the KV `id`).

Set vars in `wrangler.toml`:

- `RP_ID` — domain of the PWA (e.g. `app.example.com`), no scheme
- `APP_ORIGINS` — exact origins allowed (comma-separated), e.g. `https://app.example.com`

```bash
npm run migrate
openssl rand -base64 48 | npx wrangler secret put SESSION_SECRET
openssl rand -base64 32 | npx wrangler secret put KEK_B64
# Store the KEK backup OFFLINE. Losing it = Tier-2 sealed material is unrecoverable.
npm run deploy
curl https://bedrock-api.<your-subdomain>.workers.dev/healthz
```

## 2. Smoke checks

| Call | Expect |
|---|---|
| `GET /healthz` | `{"ok":true,...}` |
| `POST /auth/login/options` with `{}` | JSON with a `challenge` |
| `GET /vault/latest` without token | `401` |

## 3. Site

Deploy `site/` to Netlify or Cloudflare Pages. Publish directory: `site` (or `.` if you deploy from inside `site/`).

The PWA remains fully offline-capable. Sync / passkey login activates when the client
is pointed at the Worker URL (next phase).

## 4. Safety order

1. Deploy backend → smoke checks
2. Export encrypted `.bdv` from the PWA (always keep a local backup)
3. Wire the client ONLINE panel
4. Register a passkey on a throwaway vault first

## Honest status

Phase 0+1 API is implemented: auth ceremonies, refresh rotation with theft detection,
device list, sealed security inbox, and versioned vault sync (30-version history).
Client wiring and Phase 3+ (Plaid / Coinbase recon) are not in this tree yet.
