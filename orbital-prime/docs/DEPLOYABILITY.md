# Deployability — OP-01

Living score. **Not** an igloo.inc studio score.  
**Deployable** means: merge to `main` and production Netlify serves a working instrument at `/orbital` → `/orbital-prime/`, with live public connectors and no invented telemetry.

Date of this row: 2026-08-16 (SW v9 proven on deploy preview).

## Two numbers

| Number | Meaning | Now |
|---|---|---|
| **Code-ready** | Would production work if this branch merged? | **85%** |
| **Live on production `main`** | Users hitting the production Netlify domain get OP-01 | **0%** |

The second number stays 0 until PR #11 merges. That is a human/git gate, not more CSS.

**Proof, this turn:** `https://darling-kleicha-ba04ad.netlify.app/orbital` → **404**. Preview hosts serve SW `orbital-prime-v9` and `main.js?v=9`.

A prior forecast of “84 → ~90 once this commit is on preview” was too high. Preview proof closes the last **Netlify wiring** point (19 → 20). Merge is still 0 of 10, so the rubric cannot honestly sit at 90.

## Code-ready rubric (weights sum to 100)

| Gate | Weight | Score now | Why not 100 |
|---|---|---|---|
| Instrument loop (lock, FACE, gate, SGP4 table) | 25 | 24 | Starship NAME 404 is a real empty catalog |
| Netlify wiring (redirects, functions, headers) | 20 | 20 | This commit is live on deploy preview: `/orbital` 301, proxy ISS 200, unknown src 400, health all-ok, HTML no-cache, SW v9 no-store |
| Paths / PWA / SW on `/orbital-prime/` | 10 | 9 | Network-first HTML/CSS/JS on v9. Still needs a post-merge hit on the production host |
| Tests covering deploy surface | 15 | 14 | 35 deterministic tests + live CI job (continue-on-error). No Lighthouse gate |
| Ship-level a11y (contrast, focus, reduced motion) | 10 | 9 | Small status is ink-on-chip. Pinch-zoom restored. Gate-word remains colored at display size (AA large) |
| Crashers / known defects | 10 | 9 | Module-worker unsupported browsers fall back to yielding main thread |
| Merge / DNS / production cache | 10 | 0 | Not on `main`. Production `/orbital` is 404 as of 2026-08-16 |

**Code-ready = 85 / 100.**

Iteration log this turn: **78 → 84** (network-first SW, UMD worker boot, chips, zoom) then **84 → 85** (this commit proven on Netlify preview).

## Live preview evidence (commit `6fbea45`, 2026-08-16)

Host: `https://deploy-preview-11--darling-kleicha-ba04ad.netlify.app`

| Check | Result |
|---|---|
| `GET /orbital` | 301 → `/orbital-prime/` |
| `GET /orbital-prime/` | 200, `Cache-Control: no-cache`, `orbital.css?v=9`, `main.js?v=9` |
| `GET /orbital-prime/api/feed?src=iss` | 200 ISS JSON |
| `GET /orbital-prime/api/feed?src=https://evil.example` | 400 `unknown src` |
| `GET /orbital-prime/api/health` | `ok: true`, iss/tle/wx/radar/kp all ok |
| `GET /orbital-prime/api/feed?src=stations` | 200, TLE bytes |
| `GET /orbital-prime/service-worker.js` | 200, `no-store`, `CACHE = orbital-prime-v9` |
| `GET /orbital-prime/js/sat-boot.js` | 200 JavaScript |

Same v9 assets on `deploy-preview-11--dazzling-quokka-659d1b.netlify.app`.

Local instrument (Buffalo, 2026-08-16): FACE live, ISS/TLE/WX/RADAR/Kp all `live`, SGP4 residual LOCK, gate PERFECT. Starship NAME 404 is the only console error — real empty catalog.

## What would move the needle

- **85 → ~90:** the five leftover 1-point nits (Starship empty slot, Lighthouse gate, production-host SW scope, gate-word color, module-worker fallback). None of those are merge.
- **90 → 100 code-ready:** merge + one production smoke (ISS lock paints, feed proxy used, SW v9, no stale HTML). That spends the 10 merge points and the last path point.
- **Live on main 0 → 100:** merge PR #11. No further product work substitutes for that.

## Explicitly not in this percentage

Houdini, Blender, GSAP, fitted ML, Apify Store publish, custom domain DNS. Those are other products or other accounts.
