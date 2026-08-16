# Deployability — OP-01

Living score. **Not** an igloo.inc studio score.  
**Deployable** means: merge to `main` and production Netlify serves a working instrument at `/orbital` → `/orbital-prime/`, with live public connectors and no invented telemetry.

Date of this row: 2026-08-16 (SW network-first + worker UMD boot + small-text chips).

## Two numbers

| Number | Meaning | Now |
|---|---|---|
| **Code-ready** | Would production work if this branch merged? | **84%** |
| **Live on production `main`** | Users hitting the production Netlify domain get OP-01 | **0%** |

The second number stays 0 until PR #11 merges. That is a human/git gate, not more CSS.

**Proof, this turn:** `https://darling-kleicha-ba04ad.netlify.app/orbital` → **404**. Preview hosts work.

## Code-ready rubric (weights sum to 100)

| Gate | Weight | Score now | Why not 100 |
|---|---|---|---|
| Instrument loop (lock, FACE, gate, SGP4 table) | 25 | 24 | Starship NAME 404 is a real empty catalog. Worker now boots satellite.js via `Function` (tested), with main-thread fallback |
| Netlify wiring (redirects, functions, headers) | 20 | 19 | **Live preview of the previous commit proven:** `/orbital` 301, `api/feed?src=iss` 200, unknown src 400, health `ok`, HTML `Cache-Control: no-cache`, SW `no-store`. Not 20: this commit’s SW v9 is not on that preview yet |
| Paths / PWA / SW on `/orbital-prime/` | 10 | 9 | HTML/CSS/JS are **network-first** so a later production deploy is not trapped by cache-first shells. Still needs a post-merge hit on the production host |
| Tests covering deploy surface | 15 | 14 | UMD boot, SW strategy, id contract, proxy allowlist. Live HTTP job is still `continue-on-error`; no Lighthouse gate |
| Ship-level a11y (contrast, focus, reduced motion) | 10 | 9 | Small status is ink-on-chip (yellow / paper-2). Pinch-zoom restored. Gate-word remains colored at display size (AA large). Mute 5.02:1 |
| Crashers / known defects | 10 | 9 | Module-worker unsupported browsers still fall back to yielding main thread |
| Merge / DNS / production cache | 10 | 0 | Not on `main`. Production `/orbital` is 404 as of 2026-08-16 |

**Code-ready = 84 / 100.**

Previous row was **78%**. This iteration: +2 preview-proven Netlify wiring, +1 SW network-first, +1 tests, +1 a11y chips/zoom, +1 worker boot.

## Live preview evidence (2026-08-16)

Host: `https://deploy-preview-11--darling-kleicha-ba04ad.netlify.app`

| Check | Result |
|---|---|
| `GET /orbital` | 301 → `/orbital-prime/` |
| `GET /orbital-prime/` | 200, `Cache-Control: no-cache` |
| `GET /orbital-prime/api/feed?src=iss` | 200 ISS JSON |
| `GET /orbital-prime/api/feed?src=https://evil.example` | 400 `unknown src` |
| `GET /orbital-prime/api/health` | `ok: true`, iss/tle/wx/radar/kp 200 |
| `GET /orbital-prime/api/feed?src=starship` | 404 empty catalog (real) |
| `GET /orbital-prime/service-worker.js` | 200, `no-store`, was `orbital-prime-v8` at smoke time |

Same checks passed on `deploy-preview-11--dazzling-quokka-659d1b.netlify.app`.

## What would move the needle

- **84 → ~90:** this commit (SW v9, `orbital.css?v=9`, worker UMD boot) proven on a Netlify deploy preview. Still not production.
- **90 → 100 code-ready:** one production smoke after merge (ISS lock paints, feed proxy used, SW v9, no stale HTML).
- **Live on main 0 → 100:** merge PR #11. No further product work substitutes for that.

## Explicitly not in this percentage

Houdini, Blender, GSAP, fitted ML, Apify Store publish, custom domain DNS. Those are other products or other accounts.
