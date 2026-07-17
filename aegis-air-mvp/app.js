"use strict";
/* ============================================================
   Aegis Air MVP — application logic.
   Local-first: no backend, all personal data in localStorage.
   ============================================================ */

const DEFAULT_LOC = { lat: 42.9656, lon: -78.8703, label: "Kenmore / Buffalo, NY (default)" };
const FIRE_RANGE_KM = 2600;
const LS = { profile: "aegis.profile.v1", checkins: "aegis.checkins.v1", location: "aegis.location.v1" };

const SENSITIVITY_FACTORS = [
  ["asthma", "Asthma"],
  ["copd", "COPD or other chronic lung disease"],
  ["heart", "Heart or vascular condition"],
  ["pregnant", "Pregnant"],
  ["age", "Child (<18) or older adult (65+)"],
  ["outdoorWork", "Work or exercise outdoors most days"],
  ["smokeSensitive", "Past strong reactions to smoke days"],
];

const SYMPTOMS = [
  ["cough", "Cough"],
  ["wheeze", "Wheeze"],
  ["sob", "Shortness of breath with activity"],
  ["chestTight", "Chest tightness"],
  ["throat", "Throat / eye irritation"],
  ["headache", "Headache"],
  ["fatigue", "Unusual fatigue"],
];

const EMERGENCY_SYMPTOMS = [
  ["sobRest", "Severe shortness of breath at rest"],
  ["chestPain", "Chest pain or pressure"],
  ["blueLips", "Bluish lips or face"],
  ["confusion", "Confusion or fainting"],
];

/* ---------- state ---------- */
const state = {
  loc: loadJSON(LS.location) || { ...DEFAULT_LOC },
  weather: null,
  air: null,
  fires: [],
  chartMetric: "pm2_5",
  activeTab: "dashboard",
  map: null,
  mapLayers: { fires: null, plume: null, me: null },
};

/* ---------- tiny helpers ---------- */
function $(id) { return document.getElementById(id); }
function loadJSON(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
function saveJSON(k, v) { localStorage.setItem(k, JSON.stringify(v)); }
function fmt(n, d = 0) { return (n === null || n === undefined || Number.isNaN(n)) ? "–" : Number(n).toFixed(d); }
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function setStatus(msg, err) { const el = $("statusLine"); el.textContent = msg; el.className = "status" + (err ? " err" : ""); }

let toastTimer = null;
function toast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2600);
}

function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371, toR = Math.PI / 180;
  const dLat = (lat2 - lat1) * toR, dLon = (lon2 - lon1) * toR;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * toR) * Math.cos(lat2 * toR) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}
function bearingDeg(lat1, lon1, lat2, lon2) {
  const toR = Math.PI / 180;
  const y = Math.sin((lon2 - lon1) * toR) * Math.cos(lat2 * toR);
  const x = Math.cos(lat1 * toR) * Math.sin(lat2 * toR) - Math.sin(lat1 * toR) * Math.cos(lat2 * toR) * Math.cos((lon2 - lon1) * toR);
  return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}
function angleDiff(a, b) { let d = Math.abs(a - b) % 360; return d > 180 ? 360 - d : d; }
function compass16(deg) {
  const pts = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
  return pts[Math.round(deg / 22.5) % 16];
}
function destPoint(lat, lon, bearing, distKm) {
  const R = 6371, toR = Math.PI / 180, toD = 180 / Math.PI;
  const d = distKm / R, br = bearing * toR, la = lat * toR, lo = lon * toR;
  const la2 = Math.asin(Math.sin(la) * Math.cos(d) + Math.cos(la) * Math.sin(d) * Math.cos(br));
  const lo2 = lo + Math.atan2(Math.sin(br) * Math.sin(d) * Math.cos(la), Math.cos(d) - Math.sin(la) * Math.sin(la2));
  return [la2 * toD, ((lo2 * toD) + 540) % 360 - 180];
}

function aqiCategory(aqi) {
  if (aqi == null) return { name: "–", color: "#64748b" };
  if (aqi <= 50) return { name: "Good", color: "#34d399" };
  if (aqi <= 100) return { name: "Moderate", color: "#fbbf24" };
  if (aqi <= 150) return { name: "Unhealthy for sensitive groups", color: "#fb923c" };
  if (aqi <= 200) return { name: "Unhealthy", color: "#f87171" };
  if (aqi <= 300) return { name: "Very unhealthy", color: "#a78bfa" };
  return { name: "Hazardous", color: "#c084fc" };
}

/* ---------- data fetch ---------- */
async function fetchAll() {
  const { lat, lon } = state.loc;
  setStatus("Fetching live data…");
  $("btnRefresh").classList.add("spinning");

  const wxUrl = "https://api.open-meteo.com/v1/forecast"
    + `?latitude=${lat}&longitude=${lon}`
    + "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
    + "&timezone=auto";
  const aqUrl = "https://air-quality-api.open-meteo.com/v1/air-quality"
    + `?latitude=${lat}&longitude=${lon}`
    + "&current=us_aqi,pm2_5,pm10,aerosol_optical_depth"
    + "&hourly=pm2_5,us_aqi,aerosol_optical_depth"
    + "&forecast_days=4&timezone=auto";
  const fireUrl = "https://eonet.gsfc.nasa.gov/api/v3/events?category=wildfires&status=open&limit=800";

  const results = await Promise.allSettled([
    fetch(wxUrl).then(r => { if (!r.ok) throw new Error("weather HTTP " + r.status); return r.json(); }),
    fetch(aqUrl).then(r => { if (!r.ok) throw new Error("air-quality HTTP " + r.status); return r.json(); }),
    fetch(fireUrl).then(r => { if (!r.ok) throw new Error("EONET HTTP " + r.status); return r.json(); }),
  ]);

  const errs = [];
  if (results[0].status === "fulfilled") state.weather = results[0].value; else errs.push("weather");
  if (results[1].status === "fulfilled") state.air = results[1].value; else errs.push("air quality");
  if (results[2].status === "fulfilled") state.fires = filterFires(results[2].value); else errs.push("EONET fires");

  $("btnRefresh").classList.remove("spinning");
  renderAll();
  if (errs.length) {
    setStatus("Sources failed: " + errs.join(", ") + " — data may be partial", true);
    toast("Some data sources failed. Try Refresh, or serve over http:// if opened as a file.");
  } else {
    setStatus("Updated " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + " · all sources OK");
  }
}

function filterFires(eonet) {
  const { lat, lon } = state.loc;
  const out = [];
  for (const ev of (eonet.events || [])) {
    const g = (ev.geometry || []).slice(-1)[0];
    if (!g) continue;
    let fLat, fLon;
    if (g.type === "Point") { [fLon, fLat] = g.coordinates; }
    else if (g.type === "Polygon") { [fLon, fLat] = g.coordinates[0][0]; }
    else continue;
    const dist = haversineKm(lat, lon, fLat, fLon);
    if (dist > FIRE_RANGE_KM) continue;
    out.push({
      id: ev.id, title: ev.title, date: g.date, lat: fLat, lon: fLon,
      distKm: dist, bearingFromMe: bearingDeg(lat, lon, fLat, fLon),
    });
  }
  out.sort((a, b) => a.distKm - b.distKm);
  return out;
}

/* ---------- profile & check-ins ---------- */
function getProfile() { return loadJSON(LS.profile) || { factors: {}, hrBaseline: null }; }
function getCheckins() { return loadJSON(LS.checkins) || []; }

function buildProfileForm() {
  const p = getProfile();
  $("profileChecks").innerHTML = SENSITIVITY_FACTORS.map(([k, label]) =>
    `<label class="chk"><input type="checkbox" data-factor="${k}" ${p.factors[k] ? "checked" : ""}/> ${label}</label>`).join("");
  $("hrBaseline").value = p.hrBaseline ?? "";
}
function saveProfile() {
  const factors = {};
  document.querySelectorAll("#profileChecks input[data-factor]").forEach(cb => { factors[cb.dataset.factor] = cb.checked; });
  const hr = parseInt($("hrBaseline").value, 10);
  saveJSON(LS.profile, { factors, hrBaseline: Number.isFinite(hr) ? hr : null });
  toast("Profile saved locally ✓");
  renderScore();
}

function buildCheckinForm() {
  $("symptomChecks").innerHTML = SYMPTOMS.map(([k, label]) =>
    `<label class="chk"><input type="checkbox" data-sym="${k}"/> ${label}</label>`).join("");
  $("emergencyChecks").innerHTML = EMERGENCY_SYMPTOMS.map(([k, label]) =>
    `<label class="chk em"><input type="checkbox" data-esym="${k}"/> ${label}</label>`).join("");
}
function saveCheckin() {
  const symptoms = [], emergency = [];
  document.querySelectorAll("#symptomChecks input[data-sym]:checked").forEach(cb => symptoms.push(cb.dataset.sym));
  document.querySelectorAll("#emergencyChecks input[data-esym]:checked").forEach(cb => emergency.push(cb.dataset.esym));
  const hr = parseInt($("ciHr").value, 10), spo2 = parseInt($("ciSpo2").value, 10), outdoor = parseInt($("ciOutdoor").value, 10);
  const entry = {
    ts: new Date().toISOString(),
    symptoms, emergency,
    hr: Number.isFinite(hr) ? hr : null,
    spo2: Number.isFinite(spo2) ? spo2 : null,
    outdoorMin: Number.isFinite(outdoor) ? outdoor : null,
    notes: $("ciNotes").value.trim() || null,
    context: {
      aqi: state.air?.current?.us_aqi ?? null,
      pm25: state.air?.current?.pm2_5 ?? null,
      lat: state.loc.lat, lon: state.loc.lon,
    },
  };
  const list = getCheckins(); list.unshift(entry); saveJSON(LS.checkins, list.slice(0, 500));
  document.querySelectorAll("#symptomChecks input,#emergencyChecks input").forEach(cb => cb.checked = false);
  $("ciHr").value = ""; $("ciSpo2").value = ""; $("ciOutdoor").value = ""; $("ciNotes").value = "";
  toast("Check-in saved locally ✓");
  renderHistory(); renderScore();
  if (emergency.length) showEmergency();
}
function showEmergency() { $("emergencyOverlay").classList.add("show"); }
function dismissEmergency() { $("emergencyOverlay").classList.remove("show"); renderScore(); }

function latestCheckinWithin(hours) {
  const cutoff = Date.now() - hours * 3600e3;
  return getCheckins().find(c => Date.parse(c.ts) >= cutoff) || null;
}

/* ---------- risk score (fully transparent) ---------- */
function computeScore() {
  const p = getProfile();
  const cur = state.air?.current || {};
  const aqi = cur.us_aqi ?? null, pm = cur.pm2_5 ?? null;
  const wind = state.weather?.current || {};
  const rows = [];
  let emergencyActive = false;

  // 1. Air burden (0–40): linear on US AQI up to 300
  const airPts = aqi == null ? 0 : clamp(aqi, 0, 300) / 300 * 40;
  rows.push(["Air burden", aqi == null ? "AQI unavailable" : `US AQI ${Math.round(aqi)} (${aqiCategory(aqi).name}), PM2.5 ${fmt(pm, 1)} µg/m³`, airPts]);

  // 2. 12-hour trend (0–10): rising forecast PM2.5 adds points
  let trendPts = 0, trendBasis = "Forecast unavailable";
  const h = state.air?.hourly;
  if (h && pm != null) {
    const idx = currentHourIndex(h.time);
    if (idx >= 0) {
      const next12 = h.pm2_5.slice(idx + 1, idx + 13).filter(v => v != null);
      if (next12.length) {
        const peak = Math.max(...next12);
        const rise = (peak - pm) / Math.max(pm, 1);
        trendPts = clamp(rise, 0, 1) * 10;
        trendBasis = `Next-12 h peak PM2.5 ${fmt(peak, 1)} vs now ${fmt(pm, 1)} (${rise > 0 ? "+" : ""}${fmt(rise * 100, 0)}%)`;
      }
    }
  }
  rows.push(["Rising-smoke trend", trendBasis, trendPts]);

  // 3. Upwind fire proximity (0–15): local wind coming from a fire's direction
  let firePts = 0, fireBasis = "No open EONET events in range, or wind not from a fire's direction";
  const wdir = wind.wind_direction_10m, wspd = wind.wind_speed_10m;
  if (wdir != null && state.fires.length) {
    for (const f of state.fires) {
      const diff = angleDiff(wdir, f.bearingFromMe); // wind FROM ≈ direction of the fire
      if (diff <= 45) {
        const pts = (1 - f.distKm / FIRE_RANGE_KM) * Math.min(1, (wspd || 0) / 30) * 15 * (1 - diff / 45 * 0.5);
        if (pts > firePts) {
          firePts = pts;
          fireBasis = `Wind from ${compass16(wdir)} ≈ direction of “${f.title}” (${fmt(f.distKm, 0)} km, Δ${fmt(diff, 0)}°) at ${fmt(wspd, 0)} km/h`;
        }
      }
    }
  }
  rows.push(["Upwind fire proximity", fireBasis, firePts]);

  // 4. Sensitivity multiplier (applies to environment points only)
  const nFactors = Object.values(p.factors || {}).filter(Boolean).length;
  const mult = Math.min(1.6, 1 + 0.15 * nFactors);
  rows.push(["Sensitivity multiplier", `${nFactors} risk factor${nFactors === 1 ? "" : "s"} × conservative weighting → ×${mult.toFixed(2)} on environment points`, null, mult]);

  // 5. Recent symptoms (0–20), last 24 h
  const ci = latestCheckinWithin(24);
  let symPts = 0, symBasis = "No check-in in the last 24 h";
  if (ci) {
    if (ci.emergency?.length) { emergencyActive = true; }
    symPts = Math.min(20, (ci.symptoms?.length || 0) * 4);
    symBasis = (ci.symptoms?.length || 0) + " symptom(s) reported " + relTime(ci.ts);
  }
  rows.push(["Recent symptoms", symBasis, symPts]);

  // 6. Heart-rate deviation (0–10) vs your baseline; SpO2 never scored
  let hrPts = 0, hrBasis = "No recent HR, or no baseline set";
  if (ci?.hr && p.hrBaseline) {
    const dev = (ci.hr - p.hrBaseline) / p.hrBaseline;
    if (dev > 0.10) hrPts = Math.min(10, (dev - 0.10) * 100);
    hrBasis = `HR ${ci.hr} vs baseline ${p.hrBaseline} bpm (${dev > 0 ? "+" : ""}${fmt(dev * 100, 0)}%)` + (ci.spo2 ? ` · SpO₂ ${ci.spo2}% recorded, not scored` : "");
  } else if (ci?.spo2) {
    hrBasis = `SpO₂ ${ci.spo2}% recorded, not scored · no HR/baseline pair`;
  }
  rows.push(["Heart-rate deviation", hrBasis, hrPts]);

  // 7. Outdoor time today (0–5), weighted when AQI > 100
  let outPts = 0, outBasis = "No outdoor time reported";
  if (ci?.outdoorMin != null) {
    const w = (aqi != null && aqi > 100) ? 2 : 1;
    outPts = Math.min(5, ci.outdoorMin / 240 * 5 * w);
    outBasis = `${ci.outdoorMin} min outdoors` + (w > 1 ? " during AQI > 100 (×2 weight)" : "");
  }
  rows.push(["Outdoor exposure time", outBasis, outPts]);

  const envPts = airPts + trendPts + firePts;
  const total = Math.round(clamp(envPts * mult + symPts + hrPts + outPts, 0, 100));
  return { rows, total, mult, envPts, emergencyActive };
}
function relTime(iso) {
  const m = Math.round((Date.now() - Date.parse(iso)) / 60000);
  if (m < 60) return m + " min ago";
  const hh = Math.round(m / 60); return hh + " h ago";
}
function scoreCategory(t) {
  if (t < 20) return { name: "Low", color: "#34d399", msg: "Normal activities are reasonable for you today." };
  if (t < 40) return { name: "Moderate", color: "#fbbf24", msg: "Consider shorter or lighter outdoor exertion." };
  if (t < 60) return { name: "Elevated", color: "#fb923c", msg: "Limit prolonged outdoor exertion; keep reliever medication handy if prescribed." };
  if (t < 80) return { name: "High", color: "#f87171", msg: "Stay indoors with filtered air where possible; wear a well-fitted N95 if you must go out." };
  return { name: "Very high", color: "#c084fc", msg: "Avoid outdoor exposure. If symptoms worsen, contact a clinician." };
}

/* ---------- tabs ---------- */
function switchTab(name) {
  state.activeTab = name;
  document.querySelectorAll(".tab").forEach(t => {
    const on = t.dataset.tab === name;
    t.classList.toggle("active", on);
    t.setAttribute("aria-selected", on ? "true" : "false");
  });
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.id === "panel-" + name));
  if (name === "map") {
    initMapIfNeeded();
    // Leaflet needs a size recalculation after the panel becomes visible
    setTimeout(() => { state.map && state.map.invalidateSize(); }, 60);
  }
  if (name === "outlook") setTimeout(renderChart, 30);
}

/* ---------- rendering ---------- */
function renderAll() {
  renderCurrent(); renderWind(); renderFires(); renderScore(); renderHistory();
  if (state.activeTab === "map") renderMap();
  if (state.activeTab === "outlook") renderChart();
}

function renderCurrent() {
  const c = state.air?.current || {}, w = state.weather?.current || {};
  $("curAqi").textContent = c.us_aqi != null ? Math.round(c.us_aqi) : "–";
  $("curPm25").textContent = fmt(c.pm2_5, 1);
  $("curAod").textContent = fmt(c.aerosol_optical_depth, 2);
  $("curTemp").textContent = fmt(w.temperature_2m, 1);
  $("curRh").textContent = fmt(w.relative_humidity_2m, 0);
  const cat = aqiCategory(c.us_aqi);
  $("aqiChip").innerHTML = c.us_aqi != null ? `<span class="aqi-chip" style="background:${cat.color}">${cat.name}</span>` : "";
}

function renderWind() {
  const w = state.weather?.current || {};
  const dir = w.wind_direction_10m, spd = w.wind_speed_10m;
  $("windSpeed").textContent = fmt(spd, 0);
  $("windMph").textContent = spd != null ? `(${fmt(spd * 0.621371, 0)} mph)` : "";
  $("windGust").textContent = w.wind_gusts_10m != null ? `Gusts ${fmt(w.wind_gusts_10m, 0)} km/h` : "";
  if (dir != null) {
    $("windDirTxt").textContent = `${compass16(dir)} → ${compass16((dir + 180) % 360)}`;
    // arrow points where the air is going (downwind)
    $("windArrow").style.transform = `rotate(${(dir + 180) % 360}deg)`;
  } else {
    $("windDirTxt").textContent = "–";
  }
}

function renderFires() {
  $("fireCount").textContent = state.fires.length;
  const n = state.fires[0];
  $("nearestFire").textContent = n ? `${n.title} · ${fmt(n.distKm, 0)} km ${compass16(n.bearingFromMe)}` : "none in range";
  const w = state.weather?.current;
  let up = "";
  if (w?.wind_direction_10m != null) {
    const upwind = state.fires.filter(f => angleDiff(w.wind_direction_10m, f.bearingFromMe) <= 45);
    up = upwind.length
      ? `⚠ ${upwind.length} event(s) roughly upwind of you right now (closest ${fmt(upwind[0].distKm, 0)} km).`
      : "No events in your current upwind sector (±45°).";
  }
  $("fireUpwind").textContent = up;
}

/* ---------- map ---------- */
function initMapIfNeeded() {
  if (state.map || typeof L === "undefined") { renderMap(); return; }
  const { lat, lon } = state.loc;
  state.map = L.map("map", { zoomControl: true }).setView([lat, lon], 6);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(state.map);
  renderMap();
}

function renderMap() {
  if (!state.map) {
    if (typeof L === "undefined") $("map").innerHTML = "<div style='padding:20px;color:#8fa1bd'>Map library failed to load (offline or blocked). Data cards still work.</div>";
    return;
  }
  const { lat, lon } = state.loc;
  state.map.setView([lat, lon], state.map.getZoom());
  for (const k of ["fires", "plume", "me"]) {
    if (state.mapLayers[k]) { state.map.removeLayer(state.mapLayers[k]); state.mapLayers[k] = null; }
  }
  state.mapLayers.me = L.circleMarker([lat, lon], { radius: 8, color: "#22d3ee", weight: 2, fillColor: "#22d3ee", fillOpacity: .85 })
    .bindPopup("You are here").addTo(state.map);

  const fg = L.layerGroup();
  for (const f of state.fires) {
    L.circleMarker([f.lat, f.lon], { radius: 6, color: "#fb923c", weight: 1.5, fillColor: "#f97316", fillOpacity: .75 })
      .bindPopup(`<strong>${f.title}</strong><br>${fmt(f.distKm, 0)} km ${compass16(f.bearingFromMe)} of you<br><span style="font-size:.75rem">EONET curated event · ${f.date ? new Date(f.date).toLocaleDateString() : ""}</span>`)
      .addTo(fg);
  }
  state.mapLayers.fires = fg.addTo(state.map);

  // plume proxy wedge — purely visual, from local wind + PM burden
  const w = state.weather?.current, pm = state.air?.current?.pm2_5;
  if (w?.wind_direction_10m != null && w?.wind_speed_10m != null) {
    const downwind = (w.wind_direction_10m + 180) % 360;
    const lenKm = clamp(5 + w.wind_speed_10m * 1.2, 8, 60);
    const opacity = clamp((pm ?? 5) / 80, 0.06, 0.5);
    const wedge = (spreadDeg, frac) => {
      const pts = [[lat, lon]];
      for (let a = -spreadDeg; a <= spreadDeg; a += 5) pts.push(destPoint(lat, lon, (downwind + a + 360) % 360, lenKm * frac));
      return pts;
    };
    const pg = L.layerGroup();
    L.polygon(wedge(28, 1.0), { stroke: false, fillColor: "#a78bfa", fillOpacity: opacity * 0.6 }).addTo(pg);
    L.polygon(wedge(20, 0.55), { stroke: false, fillColor: "#22d3ee", fillOpacity: opacity }).addTo(pg);
    pg.eachLayer(l => l.bindTooltip("Downwind plume proxy — visual only, not transport modeling", { sticky: true }));
    state.mapLayers.plume = pg.addTo(state.map);
  }
}

/* ---------- 72-hour chart (hand-rolled canvas, no dependency) ---------- */
function currentHourIndex(times) {
  if (!times) return -1;
  const nowKey = times.find(t => Date.parse(t) <= Date.now() && Date.now() < Date.parse(t) + 3600e3);
  return nowKey ? times.indexOf(nowKey) : 0;
}
const METRIC_META = {
  pm2_5: { label: "PM2.5 µg/m³", d: 1 },
  us_aqi: { label: "US AQI", d: 0 },
  aerosol_optical_depth: { label: "Aerosol optical depth", d: 2 },
};
function aqiBandColor(metric, v) {
  if (metric === "us_aqi") {
    if (v <= 50) return "#34d399"; if (v <= 100) return "#fbbf24"; if (v <= 150) return "#fb923c";
    if (v <= 200) return "#f87171"; if (v <= 300) return "#a78bfa"; return "#c084fc";
  }
  if (metric === "pm2_5") {
    if (v <= 9) return "#34d399"; if (v <= 35.4) return "#fbbf24"; if (v <= 55.4) return "#fb923c";
    if (v <= 125.4) return "#f87171"; if (v <= 225.4) return "#a78bfa"; return "#c084fc";
  }
  return "#22d3ee";
}
function renderChart() {
  const canvas = $("chart"), ctx = canvas.getContext("2d");
  const cssW = canvas.clientWidth || canvas.parentElement.clientWidth || 600, cssH = 280;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = cssW * dpr; canvas.height = cssH * dpr; canvas.style.height = cssH + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);

  const h = state.air?.hourly, metric = state.chartMetric, meta = METRIC_META[metric];
  ctx.fillStyle = "#8fa1bd"; ctx.font = "12px sans-serif";
  if (!h || !h[metric]) { ctx.fillText("Forecast data unavailable.", 12, 30); return; }
  const idx = currentHourIndex(h.time);
  const times = h.time.slice(idx, idx + 73), vals = h[metric].slice(idx, idx + 73);
  const clean = vals.filter(v => v != null);
  if (!clean.length) { ctx.fillText("No values for this metric.", 12, 30); return; }

  const padL = 44, padR = 8, padT = 16, padB = 28;
  const plotW = cssW - padL - padR, plotH = cssH - padT - padB;
  const vMax = Math.max(...clean) * 1.15 || 1, vMin = 0;
  const x = i => padL + i / (times.length - 1) * plotW;
  const y = v => padT + (1 - (v - vMin) / (vMax - vMin)) * plotH;

  // y gridlines
  ctx.strokeStyle = "#1a2540"; ctx.lineWidth = 1; ctx.textAlign = "right";
  for (let g = 0; g <= 4; g++) {
    const v = vMin + (vMax - vMin) * g / 4, yy = y(v);
    ctx.beginPath(); ctx.moveTo(padL, yy); ctx.lineTo(cssW - padR, yy); ctx.stroke();
    ctx.fillText(v.toFixed(meta.d > 0 && vMax < 10 ? 1 : 0), padL - 6, yy + 4);
  }
  // day boundaries + labels
  ctx.textAlign = "center";
  for (let i = 0; i < times.length; i++) {
    const d = new Date(times[i]);
    if (d.getHours() === 0) {
      ctx.strokeStyle = "#26365488"; ctx.beginPath(); ctx.moveTo(x(i), padT); ctx.lineTo(x(i), cssH - padB); ctx.stroke();
      ctx.fillText(d.toLocaleDateString(undefined, { weekday: "short" }), x(i), cssH - 10);
    }
  }
  ctx.fillText("now", x(0), cssH - 10);

  // area + line
  const grad = ctx.createLinearGradient(0, padT, 0, cssH - padB);
  grad.addColorStop(0, "rgba(167,139,250,.35)"); grad.addColorStop(1, "rgba(34,211,238,.03)");
  ctx.beginPath();
  let started = false;
  for (let i = 0; i < vals.length; i++) {
    if (vals[i] == null) continue;
    if (!started) { ctx.moveTo(x(i), y(vals[i])); started = true; } else ctx.lineTo(x(i), y(vals[i]));
  }
  ctx.strokeStyle = "#22d3ee"; ctx.lineWidth = 2; ctx.stroke();
  ctx.lineTo(x(vals.length - 1), cssH - padB); ctx.lineTo(x(0), cssH - padB); ctx.closePath();
  ctx.fillStyle = grad; ctx.fill();

  // colored dots every 6 h by band
  for (let i = 0; i < vals.length; i += 6) {
    if (vals[i] == null) continue;
    ctx.beginPath(); ctx.arc(x(i), y(vals[i]), 3, 0, Math.PI * 2);
    ctx.fillStyle = aqiBandColor(metric, vals[i]); ctx.fill();
  }
  // now marker
  ctx.strokeStyle = "#e8eefa"; ctx.setLineDash([3, 3]);
  ctx.beginPath(); ctx.moveTo(x(0), padT); ctx.lineTo(x(0), cssH - padB); ctx.stroke();
  ctx.setLineDash([]);
  // title
  ctx.textAlign = "left"; ctx.fillStyle = "#8fa1bd";
  ctx.fillText(meta.label + " — next 72 h (CAMS model)", padL, 12);
}

/* ---------- score & components render ---------- */
const RING_CIRC = 2 * Math.PI * 52; // r=52 in the SVG

function renderScore() {
  const s = computeScore();
  const tbody = $("compTable").querySelector("tbody");
  tbody.innerHTML = "";
  for (const [name, basis, pts, mult] of s.rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${name}</td><td class="basis">${basis}</td>
      <td class="pts">${mult != null ? ("×" + mult.toFixed(2)) : ("+" + fmt(pts, 1))}</td>`;
    tbody.appendChild(tr);
  }
  const trT = document.createElement("tr"); trT.className = "total";
  trT.innerHTML = `<td>Total (capped at 100)</td>
    <td class="basis">(air + trend + fire) × sensitivity + symptoms + HR + outdoor</td>
    <td class="pts">${s.emergencyActive ? "—" : s.total}</td>`;
  tbody.appendChild(trT);

  const ring = $("ringProg");
  if (s.emergencyActive) {
    $("scoreNum").textContent = "—";
    $("scoreCat").textContent = "Emergency symptoms reported";
    $("scoreCat").style.color = "#f87171";
    $("scoreMsg").textContent = "No score is shown while emergency-level symptoms are active. Seek medical care.";
    ring.style.stroke = "#f87171";
    ring.style.strokeDashoffset = 0;
    return;
  }
  const cat = scoreCategory(s.total);
  $("scoreNum").textContent = s.total;
  $("scoreCat").textContent = cat.name;
  $("scoreCat").style.color = cat.color;
  $("scoreMsg").textContent = cat.msg;
  ring.style.stroke = cat.color;
  ring.style.strokeDashoffset = RING_CIRC * (1 - s.total / 100);
}

/* ---------- history ---------- */
function renderHistory() {
  const list = getCheckins();
  const host = $("historyList");
  if (!list.length) { host.innerHTML = '<div class="empty">No check-ins yet. Save one from the Check-in tab.</div>'; return; }
  const symLabel = Object.fromEntries([...SYMPTOMS, ...EMERGENCY_SYMPTOMS]);
  host.innerHTML = list.slice(0, 20).map(c => {
    const tags = [...(c.emergency || []).map(s => `<span class="em">${symLabel[s] || s}</span>`),
                  ...(c.symptoms || []).map(s => `<span>${symLabel[s] || s}</span>`)].join("");
    const vitals = [c.hr ? `HR ${c.hr}` : null, c.spo2 ? `SpO₂ ${c.spo2}%` : null, c.outdoorMin != null ? `${c.outdoorMin} min outdoors` : null]
      .filter(Boolean).join(" · ");
    return `<div class="entry">
      <div class="when">${new Date(c.ts).toLocaleString()} · AQI at entry: ${c.context?.aqi != null ? Math.round(c.context.aqi) : "–"}</div>
      <div class="tags">${tags || "<span>no symptoms</span>"}</div>
      ${vitals ? `<div class="vitals">${vitals}</div>` : ""}
      ${c.notes ? `<div class="notes">“${c.notes}”</div>` : ""}
    </div>`;
  }).join("");
}

function exportJSON() {
  const payload = {
    exportedAt: new Date().toISOString(),
    app: "aegis-air-mvp",
    location: state.loc,
    profile: getProfile(),
    checkins: getCheckins(),
    lastEnvironmentSnapshot: {
      weatherCurrent: state.weather?.current ?? null,
      airCurrent: state.air?.current ?? null,
      firesInRange: state.fires,
    },
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "aegis-air-export-" + new Date().toISOString().slice(0, 10) + ".json";
  a.click();
  URL.revokeObjectURL(a.href);
  toast("Export downloaded");
}
function clearAll() {
  if (!confirm("Delete ALL locally stored Aegis Air data (profile, check-ins, location)? This cannot be undone.")) return;
  Object.values(LS).forEach(k => localStorage.removeItem(k));
  state.loc = { ...DEFAULT_LOC };
  buildProfileForm(); renderHistory(); renderScore(); updateWhere();
  toast("All local data deleted");
}

/* ---------- location ---------- */
function updateWhere() {
  $("whereLabel").textContent = state.loc.label || `${state.loc.lat.toFixed(3)}, ${state.loc.lon.toFixed(3)}`;
}
function useGeolocation() {
  if (!navigator.geolocation) { setStatus("Geolocation not supported by this browser.", true); return; }
  setStatus("Requesting your location…");
  navigator.geolocation.getCurrentPosition(pos => {
    state.loc = {
      lat: pos.coords.latitude, lon: pos.coords.longitude,
      label: `Your location (${pos.coords.latitude.toFixed(3)}, ${pos.coords.longitude.toFixed(3)})`,
    };
    saveJSON(LS.location, state.loc);
    updateWhere(); fetchAll();
  }, err => {
    setStatus("Location denied or unavailable (" + err.message + "). Using previous location.", true);
  }, { enableHighAccuracy: false, timeout: 12000, maximumAge: 300000 });
}
function useDefault() {
  state.loc = { ...DEFAULT_LOC };
  saveJSON(LS.location, state.loc);
  updateWhere(); fetchAll();
}

/* ---------- wire-up ---------- */
document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => switchTab(t.dataset.tab)));
$("btnGeo").addEventListener("click", useGeolocation);
$("btnDefault").addEventListener("click", useDefault);
$("btnRefresh").addEventListener("click", fetchAll);
$("btnSaveProfile").addEventListener("click", saveProfile);
$("btnSaveCheckin").addEventListener("click", saveCheckin);
$("btnExport").addEventListener("click", exportJSON);
$("btnClear").addEventListener("click", clearAll);
$("btnDismissEmergency").addEventListener("click", dismissEmergency);
document.querySelectorAll(".seg .seg-btn").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".seg .seg-btn").forEach(x => x.classList.remove("active"));
  b.classList.add("active");
  state.chartMetric = b.dataset.metric;
  renderChart();
}));
window.addEventListener("resize", () => { if (state.activeTab === "outlook") renderChart(); });

/* PWA: register service worker only when actually served over HTTP(S) */
if (("serviceWorker" in navigator) && /^https?:$/.test(location.protocol)) {
  navigator.serviceWorker.register("service-worker.js").catch(() => { /* non-fatal */ });
}

/* ---------- boot ---------- */
buildProfileForm();
buildCheckinForm();
updateWhere();
renderHistory();
renderScore();
fetchAll();
