# Orbital Prime — OP-01

Public field instrument for ISS (and Celestrak station) look angles, SGP4 naked-eye passes, weather-gated go/no-go, and a documented visibility score.

No accounts. No tracking pixels. No mock telemetry. Anyone with the URL can use it.

## Use it

Production path after merge: `https://<site>/orbital` → `/orbital-prime/`

Share an observer:

```
/orbital-prime/?lat=42.8864&lon=-78.8784&sat=25544
```

GPS is optional. Buffalo is the default preset.

## Stack

| Layer | What |
|---|---|
| Client | Vanilla HTML / CSS / ES modules. No bundler. PWA shell. Self-hosted fonts. |
| Unit | `js/gl/unit.js` — WebGL raymarched OP-01 encoder driven by live AZ/EL, 2D fallback. Not a globe. |
| Propagator | `vendor/satellite.min.js` (satellite.js 5) SGP4 in the browser (`findPassesAsync` yields) |
| Edge | Netlify Functions `op-feed` (allowlisted CORS proxy + short TTL) and `op-health` |
| Headless | `node js/actor-main.js` — same observe pipeline. Apify Actor `orbital-prime-observe` when pushed |
| Score | Logistic prior on live features (`js/score.js`) — not a chatbot, not synthetic history |

## Live connectors (public, no secrets)

- Where The ISS At `GET /v1/satellites/25544`
- Celestrak GP `CATNR`, `GROUP=stations`, `NAME=STARSHIP`
- Open-Meteo current + hourly cloud / precip / visibility
- RainViewer maps + observer-centered tile
- NOAA SWPC planetary K-index (1-minute)

If a connector is down, the instrument says so. It does not invent a number.

## Run locally

```bash
cd orbital-prime
python3 -m http.server 8765
```

Open `http://127.0.0.1:8765/`. Modules will not load from `file://`.

Proxy functions only exist on Netlify. Locally the client talks to the public origins directly.

Headless (same connectors, JSON out):

```bash
cd orbital-prime
node js/actor-main.js --lat=42.8864 --lon=-78.8784 --sat=25544
```

## Tests

```bash
cd orbital-prime
node --test test/score.test.mjs test/unit.test.mjs test/css-tokens.test.mjs test/observe.test.mjs test/deploy-surface.test.mjs
# optional, hits public APIs:
node --test test/live.test.mjs
```

Live tests hit the real connectors. A failure means an upstream is down, not that the app should fake data.

## Scope

Allowed: live lock, FACE, SGP4 passes, stations catalog, weather gate, radar, Kp, sky plot, ground track, depth 1–4, AR HUD, share URL, calendar of the next computed pass, spoken FACE, optional local notifications, hero OP-01 unit (WebGL or 2D).

Forbidden: Starlink trains, accounts, secret APIs, 3D Earth hero, fake live counts, marketing pages.
