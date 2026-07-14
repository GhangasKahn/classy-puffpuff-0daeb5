# BEDROCK BACKEND — Engineering & Architecture Specification
### v1.0 · The system that turns a private terminal into a connected recon platform
**Status: design-complete · Phase 0+1 implemented in `backend/` · Author: drafted for solo operation**

> **Implementation note (repo):** Phase 0+1 (auth + Tier-1 vault sync) is live code under
> `backend/` with the PWA ONLINE panel in `site/app/`. Phases 2–6 below remain the roadmap.
> Privacy posture evolved further in `backend/ZERO-KNOWLEDGE-DOCTRINE.md` (server-side audit
> chain removed; client-side vault audit; day-coarse timestamps; sealed security inbox).
> Where this spec and the doctrine disagree, **the doctrine wins**.

---

## 0 · What this backend is for — and the one honest constraint

The PWA you have is complete as a client-only instrument: manual ledger, vault, Monte Carlo, opportunity cost, encrypted backups, BYOK AI. Everything it cannot do shares one root cause — there is no trusted machine that stays awake when your phone is in your pocket. That is the entire job of this backend. It exists to do exactly five things and nothing else:

1. **Sync** — your encrypted state on every device, with versioned history, so the phone, a laptop, and a future tablet are one terminal.
2. **Recon** — scheduled, automated pulls of balances and prices (Plaid for banks/brokerages, Coinbase read-only, market data), snapshotted daily so net worth becomes a *time series* the app never had.
3. **Auth** — real login with passkeys/WebAuthn (your hardware-key gating, done properly server-side, instead of the local theater we refused to ship).
4. **AI relay** — your existing Cloudflare proxy, promoted into the platform with the spend governor enforced server-side where it can't be bypassed.
5. **MCP** — a Model Context Protocol server exposing your financial state as scoped, read-only tools, so Claude and other agents become operators inside your system instead of tourists you paste numbers to.

The honest constraint up front, because it shapes everything: **pure zero-knowledge and automated recon are mathematically incompatible.** A server that refreshes your Plaid balances at 6 a.m. must hold a usable Plaid token at 6 a.m. — it cannot be locked under a passphrase only you know, or nothing runs while you sleep. The resolution is not to abandon zero-knowledge but to split the data into two trust tiers and never blur them. That split is the spine of this design.

---

## 1 · The Two-Tier Trust Model

**Tier 1 — The Vault (zero-knowledge, end-to-end encrypted).** Your manual financial state: ledger, accounts you typed in, vault items, goals, debts, settings, AI config. Encrypted **on the client** with your passphrase (the same AES-256-GCM + PBKDF2 construction as the `.bdv` backup — the backup format literally becomes the sync format). The server stores opaque blobs it cannot read, ever. Losing the passphrase means the data is unreadable — by you, by me, by a subpoena. That is the Monero/Sparrow tradeoff you already accepted, now extended across devices.

**Tier 2 — The Recon Layer (server-readable, server-encrypted).** Plaid access tokens, Coinbase API keys, fetched balances, price snapshots. The server can read these because it must act on them unattended. They are protected by **envelope encryption**: each user's secrets are encrypted with a per-user data key (DEK, AES-256-GCM), and the DEK is wrapped by a master key (KEK) that lives only in Worker secrets — never in the database. A database leak alone exposes nothing usable; an attacker needs the database *and* the runtime secret.

The client merges the two tiers at render time: your hand-entered truth from Tier 1, the machine-fetched balances from Tier 2, reconciled in the UI. The server never sees Tier 1; you always know Tier 2 is the part a sufficiently powerful adversary of the *server* could reach. No pretending otherwise.

---

## 2 · Stack Decision

**Primary recommendation: the Cloudflare platform, end to end.** Workers (API + MCP server), D1 (SQLite at the edge) for relational data, KV for sessions and rate-limit buckets, Cron Triggers for the recon schedule, Queues for webhook fan-out, Secrets for the KEK and provider keys. 

Why, concretely: you already operate there (the AI proxy worker is deployed and working — this is an expansion, not a migration); there are no servers to patch, which matters enormously for a solo operator whose security posture is "no unattended liabilities"; the free tier genuinely covers this workload (100k requests/day, D1's free allowance dwarfs a single-user finance app); Cloudflare has first-class support for **remote MCP servers with OAuth**, which makes Phase 5 dramatically cheaper to build; and cold starts are near-zero so the cron recon is reliable.

The honest alternative considered and declined for now: **Supabase** (Postgres, built-in auth, row-level security) is the better choice if this ever becomes a multi-user product for your family — real Postgres and RLS shine there. The cost is a second platform to operate and a heavier mental model. Single-user-first says Cloudflare; the schema below is plain SQL and ports to Postgres in an afternoon if you outgrow D1. Decision: **Cloudflare now, Supabase only if BEDROCK takes on other people's data** — at which point the responsibility model changes anyway (see §9).

Frontend stays exactly what it is: the static PWA on Netlify (or moved to Cloudflare Pages later for one-platform simplicity — optional, not required). The app gains an "online mode" but **never loses offline mode**: every server feature degrades gracefully back to the client-only behavior you have today.

---

## 3 · Security Architecture

**Threat model, stated plainly.** Adversaries considered: (a) an attacker who steals the database, (b) an attacker who steals a device, (c) an attacker on the network, (d) a malicious or compromised AI agent connected via MCP, (e) yourself, locked out. Non-goals: nation-state compromise of Cloudflare itself, and rubber-hose attacks — name them so nobody pretends.

**Authentication.** Passkeys (WebAuthn) as the primary and default — your Nothing phone's fingerprint or a YubiKey becomes the login, phishing-resistant by construction, no password to stuff. TOTP as the fallback second factor for a recovery path, plus single-use recovery codes generated at enrollment and shown once. Sessions are short-lived JWTs (15 min) with rotating refresh tokens bound to the device record; refresh reuse detection kills the whole session family (standard token-theft tripwire).

**The critical separation: login ≠ decryption.** Your passkey logs you into the *service* (Tier 2, sync transport). Your passphrase decrypts the *vault* (Tier 1). The server can reset your login; **nobody can reset your passphrase.** The UI must teach this distinction explicitly, because conflating them is how people lose data or trust.

**Cryptography.** Tier 1: client-side AES-256-GCM, key derived via PBKDF2-SHA256 at 600,000 iterations (raised from the backup's 250k; WebCrypto-native, no WASM dependency — Argon2id is theoretically better but adds a WASM supply-chain surface for marginal gain at this threat level; revisit if threat model changes). Random 16-byte salt per user, random 12-byte IV per blob, AAD binds blob version + user ID so ciphertexts can't be replayed across slots. Tier 2: per-user DEK (AES-256-GCM) generated server-side, wrapped by the KEK from Worker secrets; KEK rotation procedure documented (decrypt-DEKs/rewrap, no data re-encryption needed — that's the point of envelopes). All transport TLS 1.3; HSTS preloaded.

**Audit chain.** Every security-relevant event (login, device added, link created, token used, MCP call, sync write) appends to a hash-chained log: `h_n = SHA256(h_{n-1} ‖ canonical_event_json)`. Tampering breaks the chain visibly. This is the same audit-hash discipline as your QPE engine, applied to the platform — and the app gets a SECURITY screen that verifies the chain client-side.

**Rate limiting & abuse.** Per-IP and per-user token buckets in KV; WebAuthn challenges expire in 120 s; failed-auth lockout with exponential backoff; Cloudflare WAF in front of everything. Webhooks (Plaid) verified by signature (Plaid signs with JWT — verify `Plaid-Verification` against their JWKs) and processed via Queue so a webhook storm can't exhaust the Worker.

**Frontend hardening that the backend finally enables.** With an API of our own, the app can drop unpkg at runtime: the build gets vendored React/Babel served from the same origin with Subresource Integrity hashes — closing the CDN supply-chain hole flagged in every audit. CSP becomes enforceable: `default-src 'self'` with explicit allowances for the AI provider the user configured.

**Secrets hygiene.** Nothing sensitive in the repo; Wrangler secrets for KEK, Plaid client secret, Coinbase nothing (user-supplied), session signing key. `.dev.vars` gitignored. No analytics, no error-tracker that ships request bodies. Logs scrub tokens by construction (log token *fingerprints* — first 6 of SHA-256 — never values).

---

## 4 · Data Model (D1 / SQLite — ports cleanly to Postgres)

```sql
-- identity & devices
CREATE TABLE users (
  id TEXT PRIMARY KEY,              -- uuid
  created_at INTEGER NOT NULL,
  vault_salt BLOB NOT NULL,         -- PBKDF2 salt for Tier-1 (client-generated)
  kek_version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE credentials (          -- WebAuthn
  id TEXT PRIMARY KEY,              -- credential id (b64url)
  user_id TEXT NOT NULL REFERENCES users(id),
  public_key BLOB NOT NULL,
  sign_count INTEGER NOT NULL DEFAULT 0,
  transports TEXT, nickname TEXT, created_at INTEGER NOT NULL
);
CREATE TABLE devices (
  id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
  name TEXT, last_seen INTEGER, refresh_family TEXT NOT NULL
);

-- Tier 1: encrypted vault sync (server-opaque)
CREATE TABLE vault_blobs (
  user_id TEXT NOT NULL REFERENCES users(id),
  version INTEGER NOT NULL,         -- monotonically increasing
  ciphertext BLOB NOT NULL,         -- AES-256-GCM, client-encrypted
  iv BLOB NOT NULL, sha256 TEXT NOT NULL,
  device_id TEXT, created_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, version)
);  -- keep last 30 versions; nightly prune

-- Tier 2: recon layer (envelope-encrypted, server-usable)
CREATE TABLE user_keys (
  user_id TEXT PRIMARY KEY REFERENCES users(id),
  dek_wrapped BLOB NOT NULL,        -- DEK wrapped by KEK
  kek_version INTEGER NOT NULL
);
CREATE TABLE links (                -- one row per Plaid Item / Coinbase key
  id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
  provider TEXT NOT NULL,           -- 'plaid' | 'coinbase'
  secret_ct BLOB NOT NULL, secret_iv BLOB NOT NULL,  -- token encrypted w/ DEK
  institution TEXT, status TEXT NOT NULL DEFAULT 'active',
  created_at INTEGER NOT NULL, last_refresh INTEGER, error TEXT
);
CREATE TABLE balances_cache (
  user_id TEXT NOT NULL, link_id TEXT NOT NULL,
  account_ext_id TEXT NOT NULL,     -- provider's account id
  name TEXT, kind TEXT,             -- depository|investment|credit|crypto
  balance_ct BLOB NOT NULL, balance_iv BLOB NOT NULL,  -- value encrypted w/ DEK
  as_of INTEGER NOT NULL,
  PRIMARY KEY (user_id, link_id, account_ext_id)
);
CREATE TABLE networth_snapshots (   -- the recon time series
  user_id TEXT NOT NULL, day TEXT NOT NULL,            -- YYYY-MM-DD
  payload_ct BLOB NOT NULL, payload_iv BLOB NOT NULL,  -- {cash,invest,crypto,debt,nw}
  PRIMARY KEY (user_id, day)
);

-- platform
CREATE TABLE audit_log (
  user_id TEXT NOT NULL, seq INTEGER NOT NULL,
  event TEXT NOT NULL, detail TEXT, at INTEGER NOT NULL,
  hash TEXT NOT NULL,               -- chain: SHA256(prev_hash || event_json)
  PRIMARY KEY (user_id, seq)
);
CREATE TABLE ai_usage (
  user_id TEXT NOT NULL, day TEXT NOT NULL,
  calls INTEGER NOT NULL DEFAULT 0, cost_milli INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);
CREATE TABLE mcp_tokens (
  id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
  name TEXT NOT NULL, scopes TEXT NOT NULL,    -- 'read:networth read:positions ...'
  token_fp TEXT NOT NULL,                      -- SHA-256 fingerprint; raw shown once
  created_at INTEGER NOT NULL, last_used INTEGER, revoked INTEGER DEFAULT 0
);
```

Design notes worth their ink: balances and snapshots are stored **encrypted even though the server could read them** — defense in depth means the DEK is only unwrapped in the request/cron that needs it, and a raw D1 export is gibberish. The vault keeps thirty versions so a bad sync can always be rolled back — nothing financial is ever destructively overwritten. The snapshot table is what finally gives BEDROCK a real net-worth chart over time, fed by machines instead of memory.

---

## 5 · API Contract (Worker routes)

```
AUTH
  POST /auth/register/options      → WebAuthn creation options
  POST /auth/register/verify       → create user + credential
  POST /auth/login/options         → assertion options
  POST /auth/login/verify          → session JWT + refresh (cookie, HttpOnly)
  POST /auth/refresh               → rotate refresh, new JWT
  POST /auth/totp/enroll|verify    → fallback 2FA
  GET  /auth/devices · DELETE /auth/devices/:id

VAULT SYNC (Tier 1 — opaque blobs)
  GET  /vault/latest               → {version, sha256} (HEAD-style probe)
  GET  /vault/:version             → ciphertext blob
  POST /vault                      → push {ciphertext, iv, sha256, base_version}
                                     409 on conflict → client pulls, merges, re-pushes
  GET  /vault/history              → last 30 versions metadata

RECON (Tier 2)
  POST /links/plaid/link-token     → Plaid Link token (sandbox/dev/prod per env)
  POST /links/plaid/exchange       → public_token → access_token (encrypted, stored)
  POST /links/coinbase             → store user's read-only key (validated, encrypted)
  GET  /links · DELETE /links/:id  → list / revoke (revoke also calls provider)
  POST /recon/refresh              → on-demand refresh (rate-limited 4/hr)
  GET  /recon/balances             → decrypted-for-you current cache
  GET  /recon/series?days=365      → net-worth time series
  POST /webhooks/plaid             → signature-verified, queued

PRICES
  GET  /prices?symbols=BTC,ETH     → server-cached spot (60s TTL), keyless upstream

AI RELAY (existing proxy, promoted)
  POST /ai/chat                    → OpenAI-compatible passthrough to user's provider;
                                     spend governor enforced server-side from ai_usage

PLATFORM
  GET  /audit?after=seq            → audit events + chain verification data
  GET  /healthz                    → liveness
MCP
  /mcp                             → Streamable HTTP MCP endpoint (see §7)
```

Conflict strategy for sync, stated honestly: this is a single human on a few devices, not Google Docs. **Versioned last-write-wins with mandatory pull-before-push** (the `base_version` check) plus thirty retained versions is the right amount of engineering; CRDTs would be résumé-driven complexity here. The client UX on a 409 is: pull latest, show "this device was behind — review & re-apply," never silent loss.

---

## 6 · Provider Integrations — exactly how, and the honest costs

**Plaid (banks + brokerages).** Flow: server mints a `link_token`; the app opens Plaid Link (their drop-in UI handles bank credentials — they never touch your server); Link returns a `public_token`; server exchanges it for an `access_token` and stores it envelope-encrypted; Cron hits `/accounts/balance/get` (and `/investments/holdings/get` for brokerages) each morning; webhooks deliver out-of-band updates. Reality check on access and cost: **Sandbox is free and unrestricted** — Phase 3 builds entirely there with fake institutions. Production requires an application/review and is pay-as-you-go: balance-type products run on the order of tens of cents per connected account per month at this scale — for the handful of accounts one person links, expect **single-digit dollars a month, only when you go live**. Your real bank credentials flow through Plaid's UI, not your code; what your server holds is the revocable access token.

**Coinbase (read-only).** You generate an API key in Coinbase scoped to `wallet:accounts:read` — read-only by construction, can't trade, can't withdraw. It's submitted once over TLS, validated with a test call, envelope-encrypted, and used server-side with HMAC request signing — exactly the thing the browser must never do (Coinbase's own docs forbid client-side keys, which is why the PWA could only ever fetch public prices). Cron pulls balances alongside Plaid. Revoke any time from either side.

**Market data.** The keyless Coinbase spot endpoint the app already uses, but server-cached (60 s TTL in KV) so every device and every MCP call shares one upstream hit; equities can ride a free-tier quote API later without touching the architecture.

**AI relay.** Your `bedrock-ai-proxy.js` worker is already 80% of `/ai/chat`. The upgrade: per-user spend tracking moves into `ai_usage` so the governor is enforced where the client can't lie to it, and provider keys can optionally live server-side (envelope-encrypted) instead of in localStorage — your choice per provider.

---

## 7 · MCP Integration — agents as operators, with a leash

This is the piece that makes the platform compound: a **remote MCP server** at `/mcp` (Streamable HTTP transport) so Claude — in the app, in Claude Code, anywhere MCP reaches — can operate on your live financial state with your authorization instead of pasted screenshots.

**Exposed tools, v1 (read + compute only):**

```
get_net_worth()            → current NW + tier breakdown + as_of
get_positions()            → holdings w/ cost basis, P/L
get_balances()             → per-account cached balances
get_networth_series(days)  → the snapshot time series
run_monte_carlo(params)    → server-side sim on real numbers
opportunity_cost(amount)   → FV math on your actual surplus & return
get_debt_kill_order()      → avalanche sequence w/ payoff dates
get_goal_status()          → funding %, on-plan verdicts
```

**Auth & containment, non-negotiable:** OAuth 2.1 with PKCE for interactive connections (Cloudflare's `workers-oauth-provider` makes the Worker an OAuth server) plus long-lived **scoped tokens** you mint in the app for headless agents — shown once, stored as fingerprints, individually revocable. Scopes are read-granular (`read:networth`, `read:positions`, …) and v1 ships **zero write scopes and zero money-movement capability — there is nothing to scope because the tools don't exist.** Every MCP call lands in the audit chain with the token's name. Per-token rate limits. The standing rule, in the spec so it survives my enthusiasm and yours: **an agent can read and compute; an agent cannot transact, transfer, or link accounts.** If a write tier ever ships (e.g., "append a ledger entry"), it ships behind a separate token class with per-call confirmation in the app. The reason is the same zero-sum honesty as ever: a prompt-injected agent with write access to a finance platform is a self-inflicted wound; read-only with an audit trail is a force multiplier.

What this unlocks immediately: "Claude, how did my net worth move this quarter and what drove it?" answered from real snapshots; the Coach personas grounded in live data instead of what you remember to paste; scheduled agent reviews via Claude Code cron that end with a written brief, not an action.

---

## 8 · Run Cost — the penny-pinched truth

Cloudflare Workers free tier covers a single-user platform with room to spare (100k req/day; the cron + your devices won't touch 2k); **Workers Paid at $5/mo** is worth it on day one for Queues, higher D1 limits, and headroom — call it the platform fee. D1, KV, Queues at this scale: $0. Domain you likely already own (~$10/yr). Netlify stays free. **Plaid: $0 through the entire build (sandbox), then single-digit $/mo in production for a personal handful of accounts.** Coinbase read-only: $0. AI: whatever you already spend, now governed server-side. **Total: ~$5/mo while building; realistically $5–15/mo fully live.** No surprise infrastructure, nothing that scales against you.

---

## 9 · Legal & responsibility lines (the part that keeps you out of trouble)

This platform is designed for **your** data. The moment family members get accounts, you become a custodian of other people's financial credentials — different threat model, different obligations, and the point at which Supabase RLS, a real privacy policy, and a hard look at liability stop being optional. The spec's architecture supports that future (per-user DEKs, scoped everything), but crossing that line is a decision, not a drift. Plaid's production application will also ask what you're doing and why — answer as what this is: a personal financial dashboard. And the standing line applies to the platform as it does the app: this is research and educational tooling you operate for yourself; nothing here is financial advice, and nothing in this design moves money — by design.

---

## 10 · Build Order — phases with zero-trust gates

**Phase 0 — Foundation (a weekend).** Monorepo (`/app` PWA, `/worker` backend, `/shared` types), Wrangler config, D1 migrations from §4, CI that runs migrations + tests, secrets bootstrapped. *Gate: `/healthz` live; migrations idempotent; secrets confirmed absent from repo by grep audit.*

**Phase 1 — Auth + Vault Sync (the highest-value 20%).** WebAuthn register/login, sessions, devices; vault push/pull with versioning and 409 flow; PWA gains an ONLINE panel in Config — sign in with fingerprint, sync the same encrypted format as `.bdv`. Multi-device + automatic encrypted backup, shipped. *Gate: red-team pass on auth (replay, downgrade, refresh-reuse); sync round-trip on two devices; server storage confirmed ciphertext-only by inspection; audit chain verifies client-side.*

**Phase 2 — Prices + Snapshots + the first cron.** `/prices` cache; nightly cron computes a net-worth snapshot from synced vault metadata the *client* chooses to expose for charting (explicit opt-in — even derived numbers leaving Tier 1 is a consent moment); the app's Home gains the real time-series chart. *Gate: snapshot math matches client math to the cent; opt-in verified default-off.*

**Phase 3 — Plaid, sandbox-first.** Link flow end-to-end against fake institutions; balance + holdings refresh; webhook signature verification; reconciliation UI (machine balance vs your ledger, diffs surfaced — *that's* the recon). Production application only after the sandbox gate. *Gate: token never appears in any log (grep the tail under load); revoke works from both sides; webhook with bad signature rejected; D1 export shows only ciphertext.*

**Phase 4 — Coinbase read-only.** Key intake, validation, signed server-side calls, balances merged into recon. *Gate: write-scoped key rejected at intake; signing only server-side; revocation honored.*

**Phase 5 — MCP server.** OAuth provider, scoped tokens, the eight read tools, audit-logged calls; connect from Claude and run the first live "quarterly review by agent." *Gate: token with `read:networth` cannot call `get_positions`; revoked token dead within 60 s; injection attempt against a tool surfaces in audit; confirm zero write paths by code search.*

**Phase 6 — Hardening pass.** Vendored React/Babel + SRI, strict CSP, KEK rotation drill, restore-from-history drill, full forensic audit of the platform in the same adversarial style as the app audits — findings fixed before anything else ships.

Each phase ends deployed and useful on its own; there is no big-bang cutover, and the PWA never loses its offline soul.

---

## 11 · What happens next

The next concrete artifact is the **Phase 0+1 scaffold**: the Worker project with routes stubbed against this contract, the D1 migration files verbatim from §4, the WebAuthn ceremony implemented, and the vault sync endpoints — written here, validated structurally, deployed by you with `wrangler deploy` in minutes since I can't reach the network from this workspace. From there, every phase is a working session with its gate at the end.

*Research and educational tooling, operated by you, for you. Not financial advice — and by design, not able to move a dollar.*
