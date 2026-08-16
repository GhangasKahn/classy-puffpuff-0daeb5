const DEG = Math.PI / 180;
const RE = 6378.137;
const E2 = 6.69437999014e-3;

export const BUFFALO = { lat: 42.8864, lon: -78.8784, altKm: 0.18, name: "Buffalo" };

export const WINDS = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];

export function cardinal(az) {
  return WINDS[Math.round(((az % 360) + 360) % 360 / 22.5) % 16];
}

export function geodeticToEcef(lat, lon, altKm = 0) {
  const φ = lat * DEG, λ = lon * DEG;
  const sinφ = Math.sin(φ), cosφ = Math.cos(φ);
  const N = RE / Math.sqrt(1 - E2 * sinφ * sinφ);
  return {
    x: (N + altKm) * cosφ * Math.cos(λ),
    y: (N + altKm) * cosφ * Math.sin(λ),
    z: (N * (1 - E2) + altKm) * sinφ
  };
}

export function lookAngles(obs, sat) {
  const o = geodeticToEcef(obs.lat, obs.lon, obs.altKm || 0.18);
  const s = geodeticToEcef(sat.lat, sat.lon, sat.altKm);
  const dx = s.x - o.x, dy = s.y - o.y, dz = s.z - o.z;
  const φ = obs.lat * DEG, λ = obs.lon * DEG;
  const east = -Math.sin(λ) * dx + Math.cos(λ) * dy;
  const north = -Math.sin(φ) * Math.cos(λ) * dx - Math.sin(φ) * Math.sin(λ) * dy + Math.cos(φ) * dz;
  const up = Math.cos(φ) * Math.cos(λ) * dx + Math.cos(φ) * Math.sin(λ) * dy + Math.sin(φ) * dz;
  const range = Math.hypot(east, north, up);
  const az = (Math.atan2(east, north) / DEG + 360) % 360;
  const el = Math.atan2(up, Math.hypot(east, north)) / DEG;
  return { az, el, range };
}

export function sunAltitude(lat, lon, date) {
  const d = (Date.UTC(
    date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(),
    date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds()
  ) - Date.UTC(2000, 0, 1, 12)) / 86400000;
  const g = (357.529 + 0.98560028 * d) % 360;
  const q = (280.459 + 0.98564736 * d) % 360;
  const L = q + 1.915 * Math.sin(g * DEG) + 0.020 * Math.sin(2 * g * DEG);
  const e = 23.439 - 0.00000036 * d;
  const ra = Math.atan2(Math.cos(e * DEG) * Math.sin(L * DEG), Math.cos(L * DEG));
  const dec = Math.asin(Math.sin(e * DEG) * Math.sin(L * DEG));
  const gmst = (18.697374558 + 24.06570982441908 * d) % 24;
  const lst = ((gmst + lon / 15) % 24 + 24) % 24;
  const ha = lst * 15 * DEG - ra;
  const alt = Math.asin(
    Math.sin(lat * DEG) * Math.sin(dec) + Math.cos(lat * DEG) * Math.cos(dec) * Math.cos(ha)
  );
  return alt / DEG;
}

export function sunEciKm(date) {
  const jd = date.valueOf() / 86400000 + 2440587.5;
  const T = (jd - 2451545.0) / 36525;
  let L0 = (280.46646 + 36000.76983 * T) % 360;
  if (L0 < 0) L0 += 360;
  const M = (357.52911 + 35999.05029 * T) % 360;
  const C = (1.914602 - 0.004817 * T) * Math.sin(M * DEG) + 0.019993 * Math.sin(2 * M * DEG);
  const trueLong = (L0 + C) * DEG;
  const eps = (23.439291 - 0.0130042 * T) * DEG;
  const r = 149597870.7;
  return {
    x: r * Math.cos(trueLong),
    y: r * Math.cos(eps) * Math.sin(trueLong),
    z: r * Math.sin(eps) * Math.sin(trueLong)
  };
}

export function isEclipsed(satEci, sun) {
  const mag = Math.hypot(sun.x, sun.y, sun.z);
  const ux = sun.x / mag, uy = sun.y / mag, uz = sun.z / mag;
  const along = satEci.x * ux + satEci.y * uy + satEci.z * uz;
  if (along > 0) return false;
  const px = satEci.x - along * ux;
  const py = satEci.y - along * uy;
  const pz = satEci.z - along * uz;
  return Math.hypot(px, py, pz) < RE;
}

export function issMagnitude(rangeKm, satEci, sun) {
  const satMag = Math.hypot(satEci.x, satEci.y, satEci.z);
  const sunMag = Math.hypot(sun.x, sun.y, sun.z);
  const cosPhase = -(satEci.x * sun.x + satEci.y * sun.y + satEci.z * sun.z) / (satMag * sunMag);
  const phase = Math.acos(Math.min(1, Math.max(-1, cosPhase)));
  const phaseTerm = Math.sin(phase) + (Math.PI - phase) * Math.cos(phase);
  const extra = phaseTerm > 0 ? -1.5 * Math.log10(phaseTerm / Math.PI) : 2;
  return -1.8 + 5 * Math.log10(Math.max(rangeKm, 200) / 1000) + extra;
}

export function eyeLabel({ el, eclipsed, sunAlt }) {
  if (eclipsed) return "ECLIPSED";
  if (sunAlt >= -6) return "DAY";
  if (el >= 10) return "NAKED-EYE";
  return "LOW";
}

export function classifyWx(cloud, precip, vis) {
  if (cloud == null || Number.isNaN(cloud)) {
    return { cls: "unknown", why: "Weather unread." };
  }
  const p = precip ?? 0;
  if (cloud < 30 && p === 0 && (vis == null || vis >= 8000)) {
    return { cls: "perfect", why: `Cloud ${cloud}% · dry · vis ${vis == null ? "—" : Math.round(vis / 1000) + " km"}` };
  }
  if (cloud < 70 && p < 0.5) {
    return { cls: "marginal", why: `Cloud ${cloud}% · precip ${p} mm` };
  }
  return { cls: "obstructed", why: `Cloud ${cloud}% · precip ${p} mm` };
}

export function faceCopy({ az, el, range, label }) {
  if (el == null || Number.isNaN(el)) return "FACE — waiting for ISS lock.";
  if (el < 0) {
    return `FACE ${cardinal(az)}. Station is below the horizon (${el.toFixed(0)}°).`;
  }
  const fists = Math.max(1, Math.round(el / 10));
  const words = ["ZERO","ONE","TWO","THREE","FOUR","FIVE","SIX","SEVEN","EIGHT","NINE"];
  const fistWord = `${words[fists] || fists} ${fists === 1 ? "FIST" : "FISTS"}`;
  return `FACE ${cardinal(az)}. AZ ${az.toFixed(0)}°. EL ${el.toFixed(0)}°. ${fistWord} above the horizon. ${range.toFixed(0)} km. ${label}.`;
}

export async function fetchJson(url, timeout = 12000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeout);
  try {
    const res = await fetch(url, { signal: ctrl.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(t);
  }
}

export async function fetchText(url, timeout = 12000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeout);
  try {
    const res = await fetch(url, { signal: ctrl.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.text();
  } finally {
    clearTimeout(t);
  }
}

export function parseTle(text) {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  if (lines.length < 2) throw new Error("TLE empty");
  let l1 = lines.find((l) => l.startsWith("1 "));
  let l2 = lines.find((l) => l.startsWith("2 "));
  if (!l1 || !l2) {
    if (lines.length >= 3) { l1 = lines[1]; l2 = lines[2]; }
    else throw new Error("TLE malformed");
  }
  return { name: lines[0].startsWith("1 ") ? "ISS" : lines[0], l1, l2 };
}

export function sgp4Look(satrec, observer, date) {
  const sat = window.satellite;
  if (!sat) return null;
  const pv = sat.propagate(satrec, date);
  if (!pv.position) return null;
  const gmst = sat.gstime(date);
  const ecf = sat.eciToEcf(pv.position, gmst);
  const gd = {
    longitude: sat.degreesToRadians(observer.lon),
    latitude: sat.degreesToRadians(observer.lat),
    height: observer.altKm || 0.18
  };
  const look = sat.ecfToLookAngles(gd, ecf);
  const sun = sunEciKm(date);
  const geo = sat.eciToGeodetic(pv.position, gmst);
  return {
    az: sat.radiansToDegrees(look.azimuth),
    el: sat.radiansToDegrees(look.elevation),
    range: look.rangeSat,
    eci: pv.position,
    lat: sat.radiansToDegrees(geo.latitude),
    lon: sat.radiansToDegrees(geo.longitude),
    altKm: geo.height,
    eclipsed: isEclipsed(pv.position, sun),
    mag: issMagnitude(look.rangeSat, pv.position, sun),
    sunAlt: sunAltitude(observer.lat, observer.lon, date)
  };
}

export function findPasses(satrec, observer, hours = 36) {
  const step = 30 * 1000;
  const start = Date.now();
  const end = start + hours * 3600 * 1000;
  const passes = [];
  let cur = null;
  let prev = null;
  for (let t = start; t <= end; t += step) {
    const look = sgp4Look(satrec, observer, new Date(t));
    if (!look) continue;
    const above = look.el >= 10;
    if (above && !cur) {
      cur = {
        aos: t,
        maxEl: look.el,
        maxT: t,
        samples: [look],
        eclipsed: look.eclipsed,
        sunAlt: look.sunAlt,
        mag: look.mag
      };
    } else if (above && cur) {
      if (look.el > cur.maxEl) {
        cur.maxEl = look.el;
        cur.maxT = t;
        cur.mag = look.mag;
        cur.eclipsed = look.eclipsed;
        cur.sunAlt = look.sunAlt;
      }
      cur.samples.push(look);
    } else if (!above && cur) {
      cur.los = prev ? prev.t : t;
      cur.eye = eyeLabel({ el: cur.maxEl, eclipsed: cur.eclipsed, sunAlt: cur.sunAlt });
      passes.push(cur);
      cur = null;
    }
    prev = { t, ...look };
  }
  if (cur) {
    cur.los = end;
    cur.eye = eyeLabel({ el: cur.maxEl, eclipsed: cur.eclipsed, sunAlt: cur.sunAlt });
    passes.push(cur);
  }
  return passes;
}

export function groundTrack(satrec, minutes = 93) {
  const pts = [];
  const now = Date.now();
  for (let i = 0; i <= minutes; i += 1) {
    const look = sgp4Look(satrec, BUFFALO, new Date(now + i * 60 * 1000));
    if (look) pts.push({ lat: look.lat, lon: ((look.lon + 180) % 360 + 360) % 360 - 180 });
  }
  return pts;
}

export function tileXY(lat, lon, z) {
  const n = 2 ** z;
  const x = Math.floor((lon + 180) / 360 * n);
  const latRad = lat * DEG;
  const y = Math.floor((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2 * n);
  return { x, y, z };
}

export function fmtTime(ms, tz) {
  const d = new Date(ms);
  try {
    return d.toLocaleString(undefined, { hour: "2-digit", minute: "2-digit", month: "short", day: "numeric", timeZoneName: "short", ...(tz ? { timeZone: tz } : {}) });
  } catch {
    return d.toISOString();
  }
}

export function fmtClock(ms) {
  return new Date(ms).toISOString().replace("T", " ").slice(0, 19) + " Z";
}
