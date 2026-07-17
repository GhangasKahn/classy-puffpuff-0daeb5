# AEGIS AIR // FIELD INTEL (v2)

A local-first, mobile-friendly **personal smoke-recon instrument**: open-source satellite
imagery capture, on-device machine learning, live wildfire/wind/air telemetry, symptom
check-ins, and a transparent exposure score. Palantir-style intel console design.

Live: `/aegis-air-mvp/` on the Netlify site · companion god's-eye console at `/aegis-command/`.

## Modules

- **OVERVIEW** — exposure index (7 transparent components), auto-compiled intel briefing,
  telemetry cells, anomaly sentinel state, fire recon with k-means cluster badges
- **SAT RECON** — NASA GIBS orbital imagery (MODIS Terra true color + 7-2-1 burn bands,
  VIIRS SNPP / NOAA-20), MODIS AOD smoke overlay, EONET fire markers, 10-day date scrub
  with pass replay, and **CAPTURE FRAME**: composes visible tiles into a stamped PNG download
- **SIGNALS** — continuous PM2.5 line: 7-day model history + CAMS T+72h + on-device
  nowcast T+24h, EPA band underlays, anomaly markers, detected-event log
- **NEURAL** — the on-device ML deck (see below), all weights printed
- **LOG** — sensitivity profile, field check-ins (symptoms / HR / SpO₂ / outdoor time),
  archive with JSON export and delete-all

## On-device ML (no cloud, no keys, transparent)

| Model | Type | Trained on |
|---|---|---|
| Nowcast engine | Ridge regression (lags, trend, hour-of-day) | Past 7 days of CAMS PM2.5 at your position; holdout RMSE shown |
| Anomaly sentinel | Robust z-score (median/MAD) | Same-hour 7-day baseline; ≥2σ logs an event |
| Personal pattern learner | Logistic regression | Your own check-ins (needs ≥8 varied entries); weights + fit accuracy printed |
| Fire clustering | k-means | EONET events within 2,600 km |

All models run in the browser and print their weights. They find patterns — they are
**not medical inference** and never diagnose.

## Data sources (all open, no API keys)

- Open-Meteo Weather + Air Quality (CAMS) — modeled data, labeled as such
- NASA EONET v3 wildfire events
- NASA GIBS / Worldview satellite imagery (Terra/MODIS, Suomi-NPP & NOAA-20/VIIRS)
- OpenStreetMap / CARTO basemaps

## Important limitations

- Not a medical device; does not diagnose illness. Emergency symptoms trigger a hard stop.
- EONET is curated, not a complete hotspot feed; GIBS imagery lags ~1–2 days by satellite.
- CAMS values are modeled, not EPA AirNow regulatory observations.
- SpO₂ is recorded but never interpreted or scored. HR is used only vs your own baseline.
- All health data stays in the browser unless exported.

## Run it

```bash
cd aegis-air-mvp
python3 -m http.server 8080   # then open http://localhost:8080
```

Installable as a PWA over HTTP/HTTPS (offline app shell + cached tiles/data).
