# Aegis Air MVP

A local-first, mobile-friendly prototype for live wildfire context, wind, air quality, a 72-hour PM2.5/AQI outlook, symptom check-ins, and a transparent personal exposure-risk score.

## What works now

- Buffalo/Kenmore default location or browser geolocation
- Live Open-Meteo weather and CAMS air-quality forecasts
- NASA EONET curated wildfire events within 2,600 km
- Wind direction and speed
- 72-hour PM2.5, AQI, or aerosol-optical-depth chart
- Conservative personal sensitivity profile
- Manual symptoms, heart rate, SpO2, and outdoor-time entries
- Transparent score-component view
- Local browser storage and JSON export
- Emergency-symptom hard stop
- Installable PWA when served over HTTP/HTTPS

## Important limitations

- This is not a medical device and does not diagnose illness.
- NASA EONET is a curated event catalog, not a complete satellite hotspot feed.
- The purple/cyan map plume is a visual proxy based on local wind and particle burden. It is not NOAA HRRR-Smoke or HYSPLIT transport modeling.
- Open-Meteo/CAMS values are modeled environmental data. A later version should ingest EPA AirNow regulatory observations and local indoor sensors.
- SpO2 is recorded but deliberately not interpreted or scored. Heart rate is used only as a relative deviation from a user-entered baseline.
- Health data remains in the browser unless the user exports it.

## Project structure

```text
aegis-air-mvp/
  index.html         markup: app bar, tabbed sections, forms
  styles.css         dark glassy theme, mobile bottom tab bar
  app.js             data fetching, scoring, map, chart, storage
  manifest.json      PWA manifest
  service-worker.js  offline app shell + network-first live data
  icon.svg / icon-192.png / icon-512.png
```

On the Netlify site this deploys under `/aegis-air-mvp/` (short link: `/aegis`).

## Run it

### Simplest

Open `index.html`. Most modern browsers will load the live APIs directly. If the browser blocks network calls from a local file, use the local server below.

### Mac, Linux, or Termux

```bash
cd aegis-air-mvp
python3 -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

For another device on the same Wi-Fi, use the computer's local network address, for example:

```text
http://192.168.1.20:8080
```

### Windows

```powershell
cd aegis-air-mvp
py -m http.server 8080
```

## Next engineering milestones

1. Replace curated EONET markers with NASA FIRMS VIIRS hotspots using a user API key.
2. Add EPA AirNow regulatory-monitor observations and source labels.
3. Add true HRRR-Smoke raster tiles and forecast animation.
4. Add NOAA HYSPLIT backward trajectories for modeled source attribution.
5. Connect a local indoor PM2.5 sensor and calculate infiltration/filtration effectiveness.
6. Build a native SwiftUI version with HealthKit permissions and on-device encrypted storage.
7. Validate the personal-risk model with clinician-reviewed thresholds and time-separated data.

## Data sources

- Open-Meteo Weather API
- Open-Meteo Air Quality API using CAMS forecasts
- NASA EONET API v3
- OpenStreetMap map tiles
