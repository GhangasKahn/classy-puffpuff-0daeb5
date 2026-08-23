/* Shared observe pipeline.
   Same public connectors as the field instrument. No invented numbers. */

import { createRequire } from "node:module";
import {
  classifyWx, faceCopy, findPasses, getSatellite, lookAngles, parseAllTles,
  parseShareQuery, sgp4Look, sunAltitude
} from "./astro.js";
import { getIss, getKp, getTle, getWeather } from "./feeds.js";
import { issResidual, scorePass, wxSlice } from "./score.js";

export function bootSatellite() {
  const existing = getSatellite();
  if (existing?.twoline2satrec) return existing;
  const require = createRequire(import.meta.url);
  require("../vendor/satellite.min.js");
  const lib = getSatellite();
  if (!lib?.twoline2satrec) {
    throw new Error("satellite.js failed to boot in Node");
  }
  return lib;
}

export function validateObserveInput(raw = {}) {
  const lat = Number(raw.lat);
  const lon = Number(raw.lon);
  const altKm = raw.altKm == null ? 0.18 : Number(raw.altKm);
  const hours = raw.hours == null ? 36 : Number(raw.hours);
  const sat = raw.sat == null || raw.sat === "" ? "25544" : String(raw.sat);
  if (!Number.isFinite(lat) || Math.abs(lat) > 90) {
    return { ok: false, error: "lat must be a finite number in ±90." };
  }
  if (!Number.isFinite(lon) || Math.abs(lon) > 180) {
    return { ok: false, error: "lon must be a finite number in ±180." };
  }
  if (!Number.isFinite(altKm) || altKm < -1 || altKm > 20) {
    return { ok: false, error: "altKm out of range." };
  }
  if (!Number.isFinite(hours) || hours < 1 || hours > 72) {
    return { ok: false, error: "hours must be 1–72." };
  }
  if (!/^\d{1,8}$/.test(sat)) {
    return { ok: false, error: "sat must be a NORAD catalog number." };
  }
  return {
    ok: true,
    input: { lat, lon, altKm, hours, sat, name: raw.name || null }
  };
}

function feedError(e) {
  return { ok: false, error: e?.message || String(e) };
}

export async function observe(raw = {}) {
  const checked = validateObserveInput(raw);
  if (!checked.ok) return { ok: false, error: checked.error, generatedAt: new Date().toISOString() };
  const { lat, lon, altKm, hours, sat } = checked.input;
  const obs = { lat, lon, altKm, name: checked.input.name || "observer" };
  bootSatellite();

  const sources = {};
  const errors = {};

  const [issPack, tlePack, wxPack, kpPack] = await Promise.all([
    sat === "25544" ? getIss().catch((e) => feedError(e)) : Promise.resolve({ ok: false, skipped: true }),
    getTle(sat).catch((e) => feedError(e)),
    getWeather(lat, lon).catch((e) => feedError(e)),
    getKp().catch((e) => feedError(e))
  ]);

  let iss = null;
  if (issPack?.ok && issPack.data) {
    iss = issPack.data;
    sources.iss = issPack.url;
  } else if (issPack && !issPack.skipped) {
    errors.iss = issPack.error || "ISS feed unread.";
  }

  let catalog = [];
  let satrec = null;
  let row = null;
  if (tlePack?.ok && tlePack.data) {
    catalog = parseAllTles(tlePack.data);
    sources.tle = tlePack.url;
    row = catalog.find((s) => s.norad === sat) || catalog[0] || null;
    if (row) satrec = getSatellite().twoline2satrec(row.l1, row.l2);
  } else {
    errors.tle = tlePack?.error || "TLE unread.";
  }

  let wx = null;
  if (wxPack?.ok && wxPack.data) {
    wx = wxPack.data;
    sources.weather = wxPack.url;
  } else {
    errors.weather = wxPack?.error || "Weather unread.";
  }

  let kp = null;
  if (kpPack?.ok && Array.isArray(kpPack.data) && kpPack.data.length) {
    const last = kpPack.data[kpPack.data.length - 1];
    kp = last.kp_index ?? last.estimated_kp ?? null;
    sources.kp = kpPack.url;
  } else if (kpPack && !kpPack.ok) {
    errors.kp = kpPack.error || "Kp unread.";
  }

  const now = new Date();
  const sgp4 = satrec ? sgp4Look(satrec, obs, now) : null;
  let look = null;
  let residual = null;
  if (iss && sat === "25544") {
    look = lookAngles(obs, { lat: iss.latitude, lon: iss.longitude, altKm: iss.altitude });
    look.source = "LIVE";
    look.sunAlt = sunAltitude(obs.lat, obs.lon, now);
    look.eclipsed = iss.visibility === "eclipsed";
    if (sgp4) {
      look.eclipsed = sgp4.eclipsed;
      look.mag = sgp4.mag;
      residual = issResidual(iss, sgp4);
    }
  } else if (sgp4) {
    look = {
      az: sgp4.az,
      el: sgp4.el,
      range: sgp4.range,
      mag: sgp4.mag,
      eclipsed: sgp4.eclipsed,
      sunAlt: sgp4.sunAlt,
      source: "SGP4"
    };
  }

  const face = look
    ? faceCopy({ az: look.az, el: look.el, range: look.range, label: look.el >= 10 && !look.eclipsed && look.sunAlt < -6 ? "NAKED-EYE" : look.eclipsed ? "ECLIPSED" : look.sunAlt >= -6 ? "DAY" : "LOW" })
    : "FACE — waiting for lock.";

  const current = wx?.current;
  const gate = current
    ? classifyWx(current.cloud_cover, current.precipitation, current.visibility)
    : { cls: "unknown", why: errors.weather || "Weather unread." };

  let passes = [];
  if (satrec) {
    passes = findPasses(satrec, obs, hours).map((p) => {
      const slice = wxSlice(wx?.hourly, p.maxT);
      const sc = scorePass(p, slice, kp);
      return {
        aos: new Date(p.aos).toISOString(),
        max: new Date(p.maxT).toISOString(),
        los: new Date(p.los).toISOString(),
        maxEl: Number(p.maxEl.toFixed(2)),
        mag: p.mag == null ? null : Number(p.mag.toFixed(2)),
        eye: p.eye,
        gate: classifyWx(slice.cloud, slice.precip, slice.vis).cls,
        score: sc.pct,
        scoreIsPrior: true
      };
    });
  }

  return {
    ok: true,
    generatedAt: now.toISOString(),
    observer: { lat, lon, altKm, sat, targetName: row?.name || null },
    share: `?lat=${lat.toFixed(4)}&lon=${lon.toFixed(4)}&sat=${sat}`,
    look: look
      ? {
        az: Number(look.az.toFixed(2)),
        el: Number(look.el.toFixed(2)),
        rangeKm: Number(look.range.toFixed(1)),
        mag: look.mag == null ? null : Number(look.mag.toFixed(2)),
        source: look.source
      }
      : null,
    residual,
    face,
    gate,
    kp,
    passCount: passes.length,
    nextPass: passes.find((p) => Date.parse(p.los) > Date.now()) || null,
    passes,
    sources,
    errors,
    notes: [
      "Score is a hand-set logistic prior on live features, not a fitted model.",
      "Empty errors object means every requested connector answered.",
      "Starlink is not in this catalog."
    ]
  };
}

export { parseShareQuery };
