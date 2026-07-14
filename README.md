# BEDROCK — The Unreliable Ledger

A zero-trust, zero-knowledge personal finance system. Every balance, forecast, and
assumption stands trial — guilty until verified. Built as a local-first PWA with an
optional end-to-end-encrypted sync backend. **The app never moves money.**

## Structure

| Path | What it is |
|---|---|
| `site/` | Deployable web root: cinematic landing (`index.html`) + production PWA (`app/`). Drop on Netlify/Cloudflare Pages as-is (`netlify.toml` included). |
| `backend/` | Cloudflare Worker: WebAuthn passkey auth + zero-knowledge vault sync (D1 + KV). See its `README.md` and `ZERO-KNOWLEDGE-DOCTRINE.md`. Deploy per `docs/BEDROCK-Deploy-and-Activate.md`. |
| `sim/` | Design-spec simulations. Placeholder for v6 visual-system experiments. |
| `docs/` | Architecture, site + backend deploy runbooks, production checklist, ATELIER design protocol. |
| `legacy/` | Earlier experiments kept for reference only. |

### Docs map

| Doc | Use when |
|---|---|
| `docs/BEDROCK-Site-Deploy-and-Activate.md` | Netlify + phone install + first-week setup |
| `docs/BEDROCK-Deploy-and-Activate.md` | Cloudflare Worker Phase 0+1 go-live |
| `docs/PRODUCTION-CHECKLIST.md` | Pre-prod gate |
| `docs/BEDROCK-Backend-Architecture.md` | Full backend spec (Phases 0–6) |
| `docs/ATELIER-generative-web-design-protocol.md` | Landing / marketing design standard |
| `docs/QUANT-GOD-TIER.md` | Hedge-fund / quant LAB capability map |
| `docs/HERMES-AGENTS.md` | Opportunity-cost engineer + Hermes personas (local LLM) |
| `docs/VISUAL-SYSTEM.md` | Grunge / brutalist / TE / Off-White / Nothing design system |
| `backend/PRIVACY.md` · `ZERO-KNOWLEDGE-DOCTRINE.md` | Privacy constitution |

## Principles (the short version)

Solvency before optimization. The floor is sacred. Every purchase stands trial.
No unsourced claim survives. Backtests are guilty until proven innocent.
Forecasts are distributions, not promises. The user owns the vault.

## Crypto posture

Client-side PBKDF2 (600k iterations, OWASP minimum) + AES-256-GCM. Passkeys
authenticate to the service; the passphrase decrypts the vault. **Zero-knowledge
means zero recovery** — lose the passphrase, lose the vault. That is the design.

Read `backend/PRIVACY.md` and `backend/ZERO-KNOWLEDGE-DOCTRINE.md` before changing
anything that touches identity, logging, or ciphertext.

## Quick start

**Site (Netlify / Pages):** publish the `site/` directory. Landing at `/`, PWA at `/app/`.

**Backend (Cloudflare Worker):** see `backend/README.md` — create D1 + KV, set secrets,
migrate, deploy, smoke-check `/healthz`.

**Production gate:** `docs/PRODUCTION-CHECKLIST.md`.

**Client ONLINE panel (Config → ONLINE):** passkey register/login + encrypted vault
push/pull against Phase 0+1. Sovereign (offline) remains the default.

## Disclaimer

Research and education only. Nothing here is financial, legal, or tax advice.
