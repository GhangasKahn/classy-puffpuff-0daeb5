# BEDROCK — Production readiness checklist

Use this before calling a deploy "live."

## Backend

- [ ] `npx wrangler d1 create bedrock` + KV `SESS`; IDs in `wrangler.toml`
- [ ] `RP_ID` = production PWA domain (no scheme)
- [ ] `APP_ORIGINS` = exact HTTPS origins of the site (comma-separated)
- [ ] `SESSION_SECRET` + `KEK_B64` set via `wrangler secret put` (KEK backup offline)
- [ ] `npm run migrate` applied remote
- [ ] `npm run deploy`
- [ ] Smoke: `GET /healthz`, `POST /auth/login/options`, `GET /vault/latest` → 401
- [ ] Observability remains `enabled = false`
- [ ] Cron trigger present for inbox purge

## Site

- [ ] Netlify/Pages publish directory = `site`
- [ ] Custom domain HTTPS live; added to `APP_ORIGINS`
- [ ] Passkey register + login works on that origin (RP_ID match)
- [ ] Push/pull vault with passphrase round-trips on a throwaway vault first
- [ ] Local `.bdv` export taken before any restore overwrite
- [ ] Service worker updates (`bedrock-v4`+) after deploy

## Doctrine gates (do not ship if any fail)

- [ ] No email / name / phone fields added to schema
- [ ] No request/IP logging enabled
- [ ] Vault payloads remain client-encrypted; server stores ciphertext only
- [ ] Passphrase never sent to the API
- [ ] Plaid / recon features remain off until Phase 3 (explicit opt-in)

## Client crypto

- [ ] PBKDF2-SHA256 ≥ 600k iterations on new vaults
- [ ] Ciphertext size-bucket padding enabled (`pad: bucket-v1`)
- [ ] Conflict-safe sync (`expected_base_version` / 409 handling)
