# Orbital Prime

A field instrument for ISS look angles, SGP4 naked-eye passes, and weather-gated go/no-go.

Not a marketing site. Not a social product. Public connectors only.

## Run

Serve the folder (modules will not load from `file://`):

```bash
cd orbital-prime
python3 -m http.server 8765
```

Open `http://localhost:8765/`.

On the Netlify site: `/orbital` or `/orbital-prime/`.

## Protocol

Art direction and motion are frozen before implementation:

- `docs/ART_DIRECTION_FREEZE.md`
- `docs/MOTION_AND_COMPOSITION.md`
- `docs/PROTOCOL.md`
- `docs/META-PROMPT.md` — paste if an agent starts inventing features

## Scope

Allowed: ISS lock, FACE bearing, SGP4 passes, weather gate, RainViewer, sky plot, ground track, depth 1–4, AR HUD when the camera is honest.

Forbidden: new satellite programs, Starlink trains, accounts, secret APIs, 3D Earth hero, fake live counts.

## Connectors

- Where The ISS At ` /v1/satellites/25544`
- Celestrak GP + satellite.js SGP4
- Open-Meteo
- RainViewer
- NOAA SWPC planetary K-index
