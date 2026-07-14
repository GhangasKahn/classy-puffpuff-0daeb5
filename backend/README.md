# BEDROCK Backend — Phase 0+1 (Auth + Encrypted Vault Sync)

Cloudflare Worker · D1 · KV. Passkey (WebAuthn) auth with no email/PII, refresh-token
rotation with theft detection, envelope encryption (KEK→sealed inbox), sealed audit
signals, and Tier-1 zero-knowledge vault sync (versioned, conflict-safe, 30-version
history). Read **PRIVACY.md** first — it is the point of the system. The constitution
is **ZERO-KNOWLEDGE-DOCTRINE.md**.

## Layout

```
backend/
  src/
    index.ts    # router: /healthz, /auth/*, /vault/*
    auth.ts     # WebAuthn + refresh rotation + devices + inbox
    vault.ts    # versioned ciphertext store
    crypto.ts   # KEK seal/unseal + access JWT
    util.ts     # CORS, rate keys, helpers
  migrations/
    0001_init.sql
  wrangler.toml
```

## Deploy (~15 minutes, one time)

```bash
npm install
npx wrangler login

# 1) Create the database + KV, paste both IDs into wrangler.toml
npx wrangler d1 create bedrock
npx wrangler kv namespace create SESS

# 2) Apply the schema
npm run migrate

# 3) Secrets (generate strong, store the KEK backup OFFLINE — losing it = Tier-2 reset)
openssl rand -base64 48 | npx wrangler secret put SESSION_SECRET
openssl rand -base64 32 | npx wrangler secret put KEK_B64

# 4) Set vars in wrangler.toml: RP_ID (the app's domain) + APP_ORIGINS (exact app URLs)

# 5) Ship it
npm run deploy
curl https://bedrock-api.<your-subdomain>.workers.dev/healthz
```

## Smoke checks after deploy

- `GET /healthz` → `{"ok":true,...}`
- `POST /auth/login/options` with `{}` → JSON containing a `challenge` (proves WebAuthn
  config + KV are alive). Full ceremonies require the app client.
- `GET /vault/latest` without a token → `401` (auth wall confirmed).

## API surface (Phase 0+1)

| Method | Path | Notes |
|---|---|---|
| GET | `/healthz` | Liveness |
| POST | `/auth/register/options` | Begin passkey registration |
| POST | `/auth/register/verify` | Finish registration → session |
| POST | `/auth/login/options` | Begin assertion |
| POST | `/auth/login/verify` | Finish login → session |
| POST | `/auth/refresh` | Rotate refresh; reuse burns family |
| POST | `/auth/logout` | Revoke family / device |
| GET | `/auth/devices` | List opaque devices |
| DELETE | `/auth/devices/:id` | Remove device + revoke tokens |
| GET | `/auth/inbox` | Pull + delete sealed security signals |
| GET | `/vault/latest` | Newest ciphertext blob |
| GET | `/vault/:version` | Specific version |
| GET | `/vault/history` | Version metadata (no plaintext) |
| POST | `/vault` | Upload next version (`expected_base_version`) |

## Honest status

Type-checked + unit-tested conflict/CORS/prune logic. Client SDK (`site/app/bedrock-api.js`)
wires passkey auth and padded vault push/pull. **First Cloudflare deploy is still the first
full runtime test** for WebAuthn ceremonies. Safe order: deploy → smoke checks → register on a
throwaway vault with a local `.bdv` export in hand.

See `../docs/PRODUCTION-CHECKLIST.md`.

