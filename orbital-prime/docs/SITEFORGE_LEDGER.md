# Siteforge verification ledger — OP-01

Zero-trust. Claims that cannot be sourced are not made on the page.

## Claim ledger

| ID | Claim | Type | Source | Status |
|---|---|---|---|---|
| L1 | Public ISS position | demonstrated | `api.wheretheiss.at/v1/satellites/25544` | Live on the instrument |
| L2 | SGP4 passes | calculation | Celestrak GP TLE + satellite.js 5 in-browser | Live |
| L3 | Weather gate | calculation | Open-Meteo cloud/precip/visibility | Live |
| L4 | Pass “score” | inference / prior | `js/score.js` coefficients | Labeled prior, not ML |
| L5 | Usable by anyone | capability | Share `?lat&lon&sat`; Apify/CLI observe twin | Preview URL until `main` merge |
| L6 | igloo.inc-class studio | aspirational | — | **Not claimed** |

## Interaction ledger

| Interaction | Trigger | Purpose | Keyboard | Reduced motion |
|---|---|---|---|---|
| ISS lock / FACE | Telemetry 4s | Signature: where to look | n/a (readout) | Instant text |
| OP-01 unit | Live AZ/EL | Product object | aria-label on canvas | One frame; no idle spin |
| Pointer tilt | Pointer on unit | Camera only | n/a | Snaps |
| Location form | Submit / GPS / Buffalo | Set observer | Native form | Instant |
| Depth 1–4 | Radio keys | Density | Buttons | Instant toast |
| Observe CLI/Actor | `node js/actor-main.js` | Headless twin | CLI | n/a |

## Conversion

Primary action: set observer → read FACE → go outside. No account, no paywall, no fake scarcity.

## Unresolved

- Not merged to production `main`.
- Apify Store deploy requires `apify push` and an authenticated account (MCP server was unauthenticated in this environment).
- Compact WebGL unit is not a Houdini/Blender pipeline.
