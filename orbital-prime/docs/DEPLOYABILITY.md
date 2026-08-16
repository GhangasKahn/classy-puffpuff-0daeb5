# Deployability — OP-01

Living score. **Not** an igloo.inc studio score.  
**Deployable** means: merge to `main` and production Netlify serves a working instrument at `/orbital` → `/orbital-prime/`, with live public connectors and no invented telemetry.

Date of this row: 2026-08-16 (pass-worker + proxy tests iteration).

## Two numbers

| Number | Meaning | Now |
|---|---|---|
| **Code-ready** | Would production work if this branch merged? | **78%** |
| **Live on production `main`** | Users hitting the production Netlify domain get OP-01 | **0%** |

The second number stays 0 until PR #11 merges. That is a human/git gate, not more CSS.

## Code-ready rubric (weights sum to 100)

| Gate | Weight | Score now | Why not 100 |
|---|---|---|---|
| Instrument loop (lock, FACE, gate, SGP4 table) | 25 | 23 | Starship NAME 404 is real empty; Celestrak CORS still needs the proxy on Netlify |
| Netlify wiring (redirects, functions, headers) | 20 | 17 | Functions tested as allowlist/OPTIONS in CI, not as a live Netlify invoke |
| Paths / PWA / SW on `/orbital-prime/` | 10 | 8 | Needs a post-merge hit on the production host to prove SW scope |
| Tests covering deploy surface | 15 | 13 | Live HTTP job is continue-on-error; no Lighthouse gate |
| Ship-level a11y (contrast, focus, reduced motion) | 10 | 8 | Gate green is large-text only; quotation marks are decorative orange |
| Crashers / known defects | 10 | 9 | Module-worker unsupported browsers fall back to yielding main thread |
| Merge / DNS / production cache | 10 | 0 | Not on `main` |

**Code-ready = 78 / 100.**

## What would move the needle

- **78 → ~90:** merge preview proven on a Netlify deploy of this commit (proxy 200, `/orbital` 301, SW v8). Still not production.
- **90 → 100 code-ready:** one production smoke after merge (ISS lock paints, feed proxy used, no stale HTML).
- **Live on main 0 → 100:** merge PR #11. No further product work substitutes for that.

## Explicitly not in this percentage

Houdini, Blender, GSAP, fitted ML, Apify Store publish, custom domain DNS. Those are other products or other accounts.
