import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { parseAllTles } from "../js/astro.js";

const UA = { headers: { "User-Agent": "orbital-prime-op01-tests" } };

async function getJson(url, timeout = 15000) {
  let last;
  for (let i = 0; i < 2; i++) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeout);
    try {
      const res = await fetch(url, { ...UA, signal: ctrl.signal });
      assert.ok(res.ok, `${url} HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      last = e;
    } finally {
      clearTimeout(t);
    }
  }
  throw last;
}

async function getText(url, timeout = 12000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeout);
  try {
    const res = await fetch(url, { ...UA, signal: ctrl.signal });
    assert.ok(res.ok, `${url} HTTP ${res.status}`);
    return res.text();
  } finally {
    clearTimeout(t);
  }
}

describe("live connectors — real payloads, no fixtures", () => {
  it("Where The ISS At returns ISS 25544 with lat/lon/alt", async () => {
    const j = await getJson("https://api.wheretheiss.at/v1/satellites/25544");
    assert.equal(j.id, 25544);
    assert.equal(typeof j.latitude, "number");
    assert.equal(typeof j.longitude, "number");
    assert.ok(j.altitude > 300 && j.altitude < 500, String(j.altitude));
    assert.ok(j.timestamp > 1e9);
  });

  it("Celestrak GP ISS TLE parses to NORAD 25544", async () => {
    let text;
    try {
      text = await getText("https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle");
    } catch {
      text = await getText("https://celestrak.com/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle");
    }
    const rows = parseAllTles(text);
    const iss = rows.find((r) => r.norad === "25544");
    assert.ok(iss, "25544 missing");
    assert.match(iss.l1, /^1 25544/);
    assert.match(iss.l2, /^2 25544/);
  });

  it("Open-Meteo returns current cloud for Buffalo", async () => {
    const j = await getJson(
      "https://api.open-meteo.com/v1/forecast?latitude=42.8864&longitude=-78.8784&current=cloud_cover,precipitation,visibility&forecast_days=1"
    );
    assert.equal(typeof j.current.cloud_cover, "number");
  });

  it("RainViewer weather-maps.json has a past radar frame", async () => {
    const j = await getJson("https://api.rainviewer.com/public/weather-maps.json");
    assert.ok(j.host);
    assert.ok(Array.isArray(j.radar?.past) && j.radar.past.length > 0);
  });

  it("NOAA SWPC planetary K-index is a non-empty array", async () => {
    const rows = await getJson("https://services.swpc.noaa.gov/json/planetary_k_index_1m.json");
    assert.ok(Array.isArray(rows) && rows.length > 0);
    const last = rows[rows.length - 1];
    const kp = last.kp_index ?? last.estimated_kp;
    assert.equal(typeof kp, "number");
  });
});
