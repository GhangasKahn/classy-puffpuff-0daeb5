## What does OP-01 Observe do?

It computes **ISS / space-station look angles**, **SGP4 naked-eye passes**, and a **weather-gated go/no-go** for one observer. Same physics as the [Orbital Prime](https://github.com/GhangasKahn/classy-puffpuff-0daeb5) field instrument.

It is **not** a web scraper of private pages. It **does not** include Starlink. It **does not** invent telemetry. Connectors are public HTTP APIs: [Where The ISS At](https://wheretheiss.at/), [Celestrak GP](https://celestrak.org/), [Open-Meteo](https://open-meteo.com/), [NOAA SWPC](https://www.swpc.noaa.gov/).

## Why use OP-01 Observe?

- **Same numbers as the instrument.** FACE, residual, pass table, and the documented logistic prior live in `js/`.
- **Anyone can run it.** Input is latitude, longitude, optional NORAD id. No account on the website.
- **Schedulable.** On Apify you can run it on a cron and download JSON / CSV of the next 36 hours.
- **Honest failures.** If Celestrak or Open-Meteo is down, the record says so. It does not pad demo passes.

## What data can OP-01 Observe extract?

| Field | Type | Description |
|---|---|---|
| `look.az` / `look.el` | number | Topocentric azimuth and elevation, degrees |
| `face` | string | Spoken bearing line |
| `gate` | object | PERFECT / MARGINAL / OBSTRUCTED from live cloud, rain, visibility |
| `residual` | object | SGP4 vs live ISS GPS, kilometres (ISS only) |
| `passes[]` | array | AOS, max, LOS, elevation, class, weather gate, prior score |
| `sources` | object | Upstream URLs actually used |
| `errors` | object | Connector failures, never silent |

## How to compute ISS passes for a location

1. Set **Latitude** and **Longitude** (WGS-84). Buffalo `42.8864, -78.8784` is the instrument default.
2. Leave **sat** as `25544` for ISS, or another Celestrak `GROUP=stations` catalog number.
3. Run the Actor. Download the dataset as JSON, CSV, or Excel.
4. Open the matching instrument URL: `/orbital-prime/?lat={lat}&lon={lon}&sat={sat}`

Locally, without Apify:

```bash
cd orbital-prime
node js/actor-main.js --lat=42.8864 --lon=-78.8784 --sat=25544
```

## How much will it cost?

The run is a short HTTP fetch plus in-process SGP4 (36 hours at 30-second steps). On Apify that is a small compute-unit use, typically seconds, not a crawl. There is no per-result scrape of HTML. Public APIs are free; Apify platform time is billed by Apify, not by this project.

## Input

See the **Input** tab. Required: `lat`, `lon`. Optional: `sat` (default `25544`), `hours` (1–72, default 36), `altKm` (default 0.18).

## Output

You can download the dataset in JSON, HTML, CSV, or Excel. Each dataset row is one ≥10° pass. The key-value record `OUTPUT` is the full observe object:

```json
{
  "ok": true,
  "observer": { "lat": 42.8864, "lon": -78.8784, "sat": "25544" },
  "face": "FACE NW. Station is below the horizon (-40°).",
  "gate": { "cls": "perfect", "why": "Cloud 12% · dry · vis 20 km" },
  "passCount": 4,
  "scoreIsPrior": true
}
```

(Example shape. Live numbers change.)

## Tips

- Score is a **hand-set logistic prior**, not a trained model. The field is labeled `scoreIsPrior: true`.
- `NAME=STARSHIP` on Celestrak is often HTTP 404. That means empty, not a bug to fake.
- Do not raise `hours` above 36 unless you need it. Longer searches cost CPU, not accuracy of the current TLE.

## FAQ, disclaimers, and support

This Actor reads **public ephemeris and weather**. It does not extract private user data (emails, accounts, precise device GPS of strangers). Observer coordinates are **your input**. Treat them as personal if they are a home address.

You should not run this against catalog objects you are not allowed to publish in your jurisdiction. Starlink trains are out of scope by product law.

Issues: use the GitHub repo for the instrument. This Actor is the headless twin of `/orbital-prime/`.
