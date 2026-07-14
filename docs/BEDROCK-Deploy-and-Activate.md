# BEDROCK — Deploy and Activate (Backend)

Runbook for bringing the Phase 0+1 backend online and pointing the PWA at it.
For Netlify + phone install + first-week data setup, use
**`BEDROCK-Site-Deploy-and-Activate.md`** first. Full multi-phase design lives in
**`BEDROCK-Backend-Architecture.md`**.

Nothing here changes your existing local vault until you use Config → ONLINE.
Always export a `.bdv` before the first sync.

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

In **Config → ONLINE**, set the Worker URL, register a passkey on that origin, then push/pull
with your vault passphrase. Export a local `.bdv` first.

The PWA remains fully offline-capable. Sync is optional.

## 4. Safety order

1. Deploy backend → smoke checks
2. Export encrypted `.bdv` from the PWA (always keep a local backup)
3. Register passkey on a throwaway vault first
4. Push / pull round-trip before trusting multi-device

## 5. Production gate

Complete `docs/PRODUCTION-CHECKLIST.md` before treating a deploy as live.
