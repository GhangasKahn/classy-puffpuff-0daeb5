---
name: orbital-prime-ops
description: Operate and extend Orbital Prime (OP-01), the public ISS/station observation instrument. Use when editing orbital-prime/**, Netlify OP functions, live telemetry, SGP4, weather gate, or visibility scoring. Enforces real connectors only, no mock data, no accounts, no Starlink.
---

# Orbital Prime operations

OP-01 is a **public field instrument**, not a SaaS. Anyone uses it via URL. No login.

## Laws

1. Never invent telemetry, pass times, user counts, or “AI accuracy.”
2. Connectors only: Where The ISS At, Celestrak GP, Open-Meteo, RainViewer, NOAA SWPC.
3. `op-feed` is an allowlisted proxy, not an open proxy. Reject unknown `src`.
4. Score = logistic prior in `js/score.js` on live features. Not a chatbot.
5. Catalog = Celestrak `GROUP=stations` plus existing Starship NAME slot. Not Starlink.
6. Service worker caches the shell. Never cache live feeds.
7. Visual language: cream paper, black ink, TE orange, Off-White yellow. No HUD cyan.

## Stack map

- UI: `orbital-prime/index.html` + `styles/orbital.css`
- Boot: `js/main.js`
- Lock/passes/AR: `js/render.js`
- Physics: `js/astro.js`
- Feeds: `js/feeds.js` → proxy on Netlify, direct locally
- Score/residual: `js/score.js`
- Edge: `netlify/functions/op-feed.js`, `op-health.js`
- Tests: `node --test orbital-prime/test/*.test.mjs`

## Share format

`?lat=42.8864&lon=-78.8784&sat=25544`

## If a feed is down

Surface `live | stale | down` on `#feeds`. Keep FACE from SGP4 if TLE is alive. Do not pad with demo numbers.
