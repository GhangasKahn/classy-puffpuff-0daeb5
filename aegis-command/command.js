"use strict";
/* ============================================================
   AEGIS // COMMAND — atmospheric OSINT console.
   All feeds are open, key-free and fetched from the browser:
   Open-Meteo (met + CAMS air), NASA EONET, NWS alerts, GDELT.
   Wind field: custom canvas particle advection over a modeled
   multi-point 10 m wind grid — honest about not being HRRR.
   ============================================================ */

/* ---------------- config ---------------- */
const DEFAULT_AOI = { lat: 42.9656, lon: -78.8703 };
const FIRE_RANGE_KM = 2600;
const GRID = { nLat: 6, nLon: 7, dLat: 5.0, dLon: 7.0 };   // wind sampling grid extent (± deg)
const AQI_GRID = { n: 5, dLat: 2.4, dLon: 3.2 };
const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const CHANNELS = [
  { id: "UCJg9wBPyKMNA5sRDnvzmkdg", name: "LIVENOW FOX" },
  { id: "UCBi2mrWuNuyYy4gbM6fU18Q", name: "ABC NEWS" },
  { id: "UCeY0bbntWzzVIaj2z3QigXg", name: "NBC NEWS" },
  { id: "UC8p1vwvWtl6T73JiExfWs1g", name: "CBS NEWS" },
  { id: "UCoMdktPbSTixAyNGwb-UYkQ", name: "SKY NEWS" },
];

/* ---------------- state ---------------- */
const S = {
  aoi: { ...DEFAULT_AOI },
  map: null,
  layers: { fires: null, rings: null, plume: null, aqi: null, aoi: null, lock: null },
  show: { wind: true, aqi: true, fires: true, rings: true, plume: true },
  wx: null, air: null,
  fires: [],
  windGrid: null,          // {lat0, lon0, dLat, dLon, nLat, nLon, u[], v[]}
  particles: [],
  raf: null,
  paused: false,
  bootT: Date.now(),
  aoiMode: false,
  selFire: null,
  timers: [],
};

/* ---------------- utils ---------------- */
const $ = (id) => document.getElementById(id);
const fmt = (n, d = 0) => (n == null || Number.isNaN(n) ? "—" : Number(n).toFixed(d));
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const toR = Math.PI / 180;

function haversineKm(a, b, c, d) {
  const p = Math.sin((c - a) * toR / 2) ** 2 + Math.cos(a * toR) * Math.cos(c * toR) * Math.sin((d - b) * toR / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(p));
}
function bearingDeg(a, b, c, d) {
  const y = Math.sin((d - b) * toR) * Math.cos(c * toR);
  const x = Math.cos(a * toR) * Math.sin(c * toR) - Math.sin(a * toR) * Math.cos(c * toR) * Math.cos((d - b) * toR);
  return (Math.atan2(y, x) / toR + 360) % 360;
}
const angleDiff = (a, b) => { const d = Math.abs(a - b) % 360; return d > 180 ? 360 - d : d; };
const compass16 = (deg) => deg == null ? "—" :
  ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"][Math.round(deg / 22.5) % 16];
function destPoint(lat, lon, brg, km) {
  const d = km / 6371, br = brg * toR, la = lat * toR;
  const la2 = Math.asin(Math.sin(la) * Math.cos(d) + Math.cos(la) * Math.sin(d) * Math.cos(br));
  const lo2 = lon * toR + Math.atan2(Math.sin(br) * Math.sin(d) * Math.cos(la), Math.cos(d) - Math.sin(la) * Math.sin(la2));
  return [la2 / toR, ((lo2 / toR) + 540) % 360 - 180];
}
function aqiColor(v) {
  if (v == null) return "#5f7396";
  if (v <= 50) return "#38e6a1"; if (v <= 100) return "#ffd454";
  if (v <= 150) return "#ffb454"; if (v <= 200) return "#ff4655";
  if (v <= 300) return "#8f7bff"; return "#c96bff";
}

/* ---------------- event log & ticker ---------------- */
function log(msg, cls = "") {
  const el = $("eventLog");
  const t = new Date().toISOString().slice(11, 19);
  const row = document.createElement("div");
  row.innerHTML = `<span class="t">${t}Z</span> <span class="${cls}">${msg}</span>`;
  el.prepend(row);
  while (el.children.length > 90) el.removeChild(el.lastChild);
}
function srcStatus(key, ok) {
  const el = document.querySelector(`#srcRow [data-src="${key}"]`);
  if (el) el.className = ok ? "ok" : "err";
}

/* ---------------- clocks ---------------- */
function startClocks() {
  const tick = () => {
    const now = new Date();
    $("zChip").textContent = "Z " + now.toISOString().slice(11, 19);
    $("lChip").textContent = "L " + now.toTimeString().slice(0, 8);
    const s = Math.floor((Date.now() - S.bootT) / 1000);
    $("metChip").textContent = `MET T+${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
  };
  tick();
  S.timers.push(setInterval(tick, 1000));
}

/* ---------------- map ---------------- */
function initMap() {
  S.map = L.map("map", { zoomControl: true, attributionControl: true, worldCopyJump: true })
    .setView([S.aoi.lat, S.aoi.lon], 5);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 18, subdomains: "abcd",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
  }).addTo(S.map);

  S.map.on("movestart zoomstart", () => { S.paused = true; clearWindCanvas(); });
  S.map.on("moveend zoomend", () => { S.paused = false; seedParticles(); });
  S.map.on("click", (e) => {
    if (!S.aoiMode) return;
    setAoi(e.latlng.lat, e.latlng.lng, "MANUAL AOI SET");
    toggleAoiMode(false);
  });
  drawAoiMarker();
}

function drawAoiMarker() {
  if (S.layers.aoi) S.map.removeLayer(S.layers.aoi);
  S.layers.aoi = L.marker([S.aoi.lat, S.aoi.lon], {
    icon: L.divIcon({ className: "aoi-marker", html: '<span class="am-x">⌖</span>', iconSize: [20, 20], iconAnchor: [10, 12] }),
    interactive: false,
  }).addTo(S.map);
  $("aoiChip").textContent = `AOI ${Math.abs(S.aoi.lat).toFixed(4)}${S.aoi.lat >= 0 ? "N" : "S"} ${Math.abs(S.aoi.lon).toFixed(4)}${S.aoi.lon >= 0 ? "E" : "W"}`;
}

function drawRings() {
  if (S.layers.rings) S.map.removeLayer(S.layers.rings);
  if (!S.show.rings) return;
  const g = L.layerGroup();
  for (const km of [500, 1000, 2000]) {
    L.circle([S.aoi.lat, S.aoi.lon], {
      radius: km * 1000, color: "#1e2f52", weight: 1, dashArray: "6 8", fill: false, interactive: false,
    }).addTo(g);
    const [la, lo] = destPoint(S.aoi.lat, S.aoi.lon, 90, km);
    L.marker([la, lo], {
      icon: L.divIcon({ className: "", html: `<span style="color:#31445f;font:9px 'IBM Plex Mono',monospace">${km} KM</span>`, iconSize: [50, 12] }),
      interactive: false,
    }).addTo(g);
  }
  S.layers.rings = g.addTo(S.map);
}

function drawPlume() {
  if (S.layers.plume) S.map.removeLayer(S.layers.plume);
  if (!S.show.plume) return;
  const w = S.wx?.current, pm = S.air?.current?.pm2_5;
  if (w?.wind_direction_10m == null) return;
  const downwind = (w.wind_direction_10m + 180) % 360;
  const lenKm = clamp(20 + (w.wind_speed_10m ?? 10) * 4, 40, 260);
  const op = clamp((pm ?? 5) / 80, 0.05, 0.4);
  const wedge = (spread, frac) => {
    const pts = [[S.aoi.lat, S.aoi.lon]];
    for (let a = -spread; a <= spread; a += 5) pts.push(destPoint(S.aoi.lat, S.aoi.lon, (downwind + a + 360) % 360, lenKm * frac));
    return pts;
  };
  const g = L.layerGroup();
  L.polygon(wedge(26, 1), { stroke: false, fillColor: "#8f7bff", fillOpacity: op * 0.55, interactive: false }).addTo(g);
  L.polygon(wedge(18, 0.55), { stroke: false, fillColor: "#2ee6ff", fillOpacity: op, interactive: false }).addTo(g);
  S.layers.plume = g.addTo(S.map);
}

function drawFires() {
  if (S.layers.fires) S.map.removeLayer(S.layers.fires);
  if (!S.show.fires) return;
  const wdir = S.wx?.current?.wind_direction_10m;
  const g = L.layerGroup();
  for (const f of S.fires.slice(0, 300)) {
    const upwind = wdir != null && angleDiff(wdir, f.brg) <= 45;
    f.upwind = upwind;
    const m = L.marker([f.lat, f.lon], {
      icon: L.divIcon({
        className: "",
        html: `<div class="fire-marker${upwind ? " upwind" : ""}" style="width:18px;height:18px"><span class="fm-ring"></span><span class="fm-core"></span></div>`,
        iconSize: [18, 18], iconAnchor: [9, 9],
      }),
    });
    m.on("click", () => lockFire(f));
    m.addTo(g);
  }
  S.layers.fires = g.addTo(S.map);
}

function drawAqiGrid(cells) {
  if (S.layers.aqi) S.map.removeLayer(S.layers.aqi);
  if (!S.show.aqi || !cells) return;
  const g = L.layerGroup();
  for (const c of cells) {
    if (c.aqi == null) continue;
    L.circleMarker([c.lat, c.lon], {
      radius: 13, stroke: false, fillColor: aqiColor(c.aqi), fillOpacity: 0.16, interactive: false,
    }).addTo(g);
    L.marker([c.lat, c.lon], {
      icon: L.divIcon({
        className: "",
        html: `<span style="color:${aqiColor(c.aqi)};font:10px 'IBM Plex Mono',monospace;text-shadow:0 0 4px #000">${Math.round(c.aqi)}</span>`,
        iconSize: [26, 12], iconAnchor: [13, 6],
      }), interactive: false,
    }).addTo(g);
  }
  S.layers.aqi = g.addTo(S.map);
}

/* target lock — range/bearing line + info card */
function lockFire(f) {
  S.selFire = f;
  if (S.layers.lock) S.map.removeLayer(S.layers.lock);
  const g = L.layerGroup();
  L.polyline([[S.aoi.lat, S.aoi.lon], [f.lat, f.lon]], {
    color: f.upwind ? "#ffb454" : "#2ee6ff", weight: 1, dashArray: "4 6", interactive: false,
  }).addTo(g);
  S.layers.lock = g.addTo(S.map);
  const el = $("lockinfo");
  el.hidden = false;
  el.innerHTML = `
    <div class="lk-t">◤ TARGET LOCK ${f.upwind ? "· UPWIND SECTOR ⚠" : ""}</div>
    <div class="lk-n">${f.title}</div>
    <div class="lk-d">RNG ${fmt(f.dist, 0)} KM · BRG ${fmt(f.brg, 0)}° ${compass16(f.brg)} · SRC EONET</div>
    <div class="lk-d">LAST GEOMETRY ${f.date ? new Date(f.date).toISOString().slice(0, 10) : "—"}</div>`;
  document.querySelectorAll(".fire-row").forEach(r => r.classList.toggle("sel", r.dataset.id === f.id));
  log(`TARGET LOCK — ${f.title.toUpperCase().slice(0, 40)} @ ${fmt(f.dist, 0)} KM`, f.upwind ? "warn" : "");
}

/* ---------------- wind particle field ---------------- */
const canvas = $("windCanvas");
const wctx = canvas.getContext("2d");

function sizeCanvas() {
  const r = canvas.parentElement.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = r.width * dpr; canvas.height = r.height * dpr;
  canvas.style.width = r.width + "px"; canvas.style.height = r.height + "px";
  wctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
function clearWindCanvas() { wctx.clearRect(0, 0, canvas.width, canvas.height); }

function gridVector(lat, lon) {
  const g = S.windGrid;
  if (!g) return null;
  const fy = (lat - g.lat0) / g.dLat, fx = (lon - g.lon0) / g.dLon;
  if (fx < 0 || fy < 0 || fx > g.nLon - 1 || fy > g.nLat - 1) return null;
  const x0 = Math.floor(fx), y0 = Math.floor(fy);
  const x1 = Math.min(x0 + 1, g.nLon - 1), y1 = Math.min(y0 + 1, g.nLat - 1);
  const tx = fx - x0, ty = fy - y0;
  const idx = (y, x) => y * g.nLon + x;
  const lerp = (a, b, t) => a + (b - a) * t;
  const u = lerp(lerp(g.u[idx(y0, x0)], g.u[idx(y0, x1)], tx), lerp(g.u[idx(y1, x0)], g.u[idx(y1, x1)], tx), ty);
  const v = lerp(lerp(g.v[idx(y0, x0)], g.v[idx(y0, x1)], tx), lerp(g.v[idx(y1, x0)], g.v[idx(y1, x1)], tx), ty);
  return { u, v }; // km/h, east & north components
}

function seedParticles() {
  if (!S.windGrid || !S.map) return;
  const b = S.map.getBounds();
  const n = REDUCED ? 0 : Math.min(1300, Math.round((canvas.clientWidth * canvas.clientHeight) / 900));
  S.particles = Array.from({ length: n }, () => spawn(b));
  if (REDUCED) drawStaticArrows();
}
function spawn(b) {
  return {
    lat: b.getSouth() + Math.random() * (b.getNorth() - b.getSouth()),
    lon: b.getWest() + Math.random() * (b.getEast() - b.getWest()),
    age: Math.random() * 140 | 0,
    px: null, py: null,
  };
}

function stepParticles() {
  S.raf = requestAnimationFrame(stepParticles);
  if (S.paused || !S.show.wind || !S.windGrid || document.hidden) return;

  // fade previous frame (trail effect)
  wctx.globalCompositeOperation = "destination-out";
  wctx.fillStyle = "rgba(0,0,0,0.07)";
  wctx.fillRect(0, 0, canvas.clientWidth, canvas.clientHeight);
  wctx.globalCompositeOperation = "source-over";

  const b = S.map.getBounds();
  const zoomK = Math.pow(2, S.map.getZoom() - 5);
  const K = 0.00045 * clamp(1 / zoomK, 0.12, 2.5); // advection scale: deg per (km/h · frame)

  wctx.lineWidth = 1.1;
  for (const p of S.particles) {
    const vec = gridVector(p.lat, p.lon);
    if (!vec || ++p.age > 160) { Object.assign(p, spawn(b)); continue; }
    const nlat = p.lat + vec.v * K;
    const nlon = p.lon + vec.u * K / Math.max(Math.cos(p.lat * toR), 0.2);
    const a = S.map.latLngToContainerPoint([p.lat, p.lon]);
    const c = S.map.latLngToContainerPoint([nlat, nlon]);
    p.lat = nlat; p.lon = nlon;
    if (c.x < -30 || c.y < -30 || c.x > canvas.clientWidth + 30 || c.y > canvas.clientHeight + 30) {
      Object.assign(p, spawn(b)); continue;
    }
    const spd = Math.hypot(vec.u, vec.v);
    wctx.strokeStyle = spd > 28 ? "rgba(255,180,84,0.55)" : "rgba(46,230,255,0.42)";
    wctx.beginPath(); wctx.moveTo(a.x, a.y); wctx.lineTo(c.x, c.y); wctx.stroke();
  }
}

function drawStaticArrows() {
  // reduced motion: one calm frame of arrows instead of animation
  clearWindCanvas();
  if (!S.windGrid) return;
  const g = S.windGrid;
  wctx.strokeStyle = "rgba(46,230,255,0.5)"; wctx.fillStyle = "rgba(46,230,255,0.5)"; wctx.lineWidth = 1;
  for (let y = 0; y < g.nLat; y++) for (let x = 0; x < g.nLon; x++) {
    const lat = g.lat0 + y * g.dLat, lon = g.lon0 + x * g.dLon;
    const u = g.u[y * g.nLon + x], v = g.v[y * g.nLon + x];
    const p = S.map.latLngToContainerPoint([lat, lon]);
    const ang = Math.atan2(-v, u), len = clamp(Math.hypot(u, v), 4, 30);
    wctx.beginPath(); wctx.moveTo(p.x, p.y);
    wctx.lineTo(p.x + Math.cos(ang) * len, p.y + Math.sin(ang) * len); wctx.stroke();
  }
}

/* ---------------- data fetchers ---------------- */
async function fetchCore() {
  const { lat, lon } = S.aoi;
  try {
    const [wx, air] = await Promise.all([
      fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m&timezone=auto`).then(r => r.json()),
      fetch(`https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&current=us_aqi,pm2_5,pm10,aerosol_optical_depth&hourly=pm2_5,us_aqi&forecast_days=4&timezone=auto`).then(r => r.json()),
    ]);
    S.wx = wx; S.air = air;
    srcStatus("wx", true); srcStatus("aq", true);
    renderAtmo(); drawPlume(); renderAti();
    log("MET + CAMS TELEMETRY REFRESHED", "ok");
  } catch {
    srcStatus("wx", false); srcStatus("aq", false);
    log("MET/CAMS FETCH FAILED", "err");
  }
}

async function fetchWindGrid() {
  const { lat, lon } = S.aoi;
  const lat0 = lat - GRID.dLat, lon0 = lon - GRID.dLon;
  const stepLat = (2 * GRID.dLat) / (GRID.nLat - 1), stepLon = (2 * GRID.dLon) / (GRID.nLon - 1);
  const lats = [], lons = [];
  for (let y = 0; y < GRID.nLat; y++) for (let x = 0; x < GRID.nLon; x++) {
    lats.push((lat0 + y * stepLat).toFixed(3)); lons.push((lon0 + x * stepLon).toFixed(3));
  }
  try {
    const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lats.join(",")}&longitude=${lons.join(",")}&current=wind_speed_10m,wind_direction_10m`).then(r => r.json());
    const arr = Array.isArray(res) ? res : [res];
    const u = [], v = [];
    for (const cell of arr) {
      const spd = cell?.current?.wind_speed_10m ?? 0, dir = cell?.current?.wind_direction_10m ?? 0;
      u.push(-spd * Math.sin(dir * toR)); // wind FROM dir → u east component
      v.push(-spd * Math.cos(dir * toR));
    }
    S.windGrid = { lat0, lon0, dLat: stepLat, dLon: stepLon, nLat: GRID.nLat, nLon: GRID.nLon, u, v };
    srcStatus("grid", true);
    seedParticles();
    log(`WIND FIELD SAMPLED — ${arr.length} NODES / ${GRID.dLat * 2}°×${GRID.dLon * 2}°`, "ok");
  } catch {
    srcStatus("grid", false);
    log("WIND FIELD SAMPLING FAILED", "err");
  }
}

async function fetchAqiGrid() {
  const { lat, lon } = S.aoi;
  const n = AQI_GRID.n;
  const lats = [], lons = [];
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    lats.push((lat - AQI_GRID.dLat + y * (2 * AQI_GRID.dLat / (n - 1))).toFixed(3));
    lons.push((lon - AQI_GRID.dLon + x * (2 * AQI_GRID.dLon / (n - 1))).toFixed(3));
  }
  try {
    const res = await fetch(`https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lats.join(",")}&longitude=${lons.join(",")}&current=us_aqi`).then(r => r.json());
    const arr = Array.isArray(res) ? res : [res];
    const cells = arr.map((c, i) => ({ lat: +lats[i], lon: +lons[i], aqi: c?.current?.us_aqi ?? null }));
    drawAqiGrid(cells);
    log(`AQI SURFACE SAMPLED — ${cells.length} NODES`, "ok");
  } catch {
    log("AQI SURFACE SAMPLING FAILED", "err");
  }
}

async function fetchFires() {
  try {
    const res = await fetch("https://eonet.gsfc.nasa.gov/api/v3/events?category=wildfires&status=open&limit=800").then(r => r.json());
    const out = [];
    for (const ev of res.events || []) {
      const g = (ev.geometry || []).slice(-1)[0];
      if (!g) continue;
      let la, lo;
      if (g.type === "Point") [lo, la] = g.coordinates;
      else if (g.type === "Polygon") [lo, la] = g.coordinates[0][0];
      else continue;
      const dist = haversineKm(S.aoi.lat, S.aoi.lon, la, lo);
      if (dist > FIRE_RANGE_KM) continue;
      out.push({ id: ev.id, title: ev.title, date: g.date, lat: la, lon: lo, dist, brg: bearingDeg(S.aoi.lat, S.aoi.lon, la, lo) });
    }
    out.sort((a, b) => a.dist - b.dist);
    S.fires = out;
    srcStatus("eonet", true);
    drawFires(); renderFireList(); renderAti();
    log(`EONET SWEEP COMPLETE — ${out.length} OPEN EVENTS ≤ ${FIRE_RANGE_KM} KM`, "ok");
  } catch {
    srcStatus("eonet", false);
    log("EONET SWEEP FAILED", "err");
  }
}

async function fetchAlerts() {
  try {
    const events = ["Red Flag Warning", "Fire Weather Watch", "Air Quality Alert", "Dense Smoke Advisory", "Extreme Fire Danger"];
    const res = await fetch(`https://api.weather.gov/alerts/active?event=${encodeURIComponent(events.join(","))}`,
      { headers: { Accept: "application/geo+json" } }).then(r => r.json());
    const feats = res.features || [];
    srcStatus("nws", true);
    renderAlerts(feats);
    log(`NWS ALERT WIRE — ${feats.length} ACTIVE FIRE/AIR PRODUCTS (US)`, feats.length ? "warn" : "ok");
  } catch {
    srcStatus("nws", false);
    renderAlerts(null);
    log("NWS ALERT WIRE FAILED", "err");
  }
}

async function fetchWire() {
  try {
    const q = encodeURIComponent('(wildfire OR "wildfire smoke" OR "air quality" OR "smoke plume" OR evacuation) sourcelang:eng');
    const res = await fetch(`https://api.gdeltproject.org/api/v2/doc/doc?query=${q}&mode=ArtList&format=json&maxrecords=36&timespan=1D&sort=DateDesc`).then(r => {
      if (!r.ok) throw new Error("gdelt " + r.status);
      return r.json();
    });
    const arts = (res.articles || []).filter(a => a.title);
    srcStatus("gdelt", true);
    renderWire(arts);
    log(`GDELT WIRE SYNCED — ${arts.length} ARTICLES / 24H`, "ok");
  } catch {
    srcStatus("gdelt", false);
    renderWire(null);
    log("GDELT WIRE UNAVAILABLE (RATE LIMIT LIKELY) — RETRY IN 5 MIN", "warn");
  }
}

/* ---------------- renderers ---------------- */
function renderAtmo() {
  const a = S.air?.current || {}, w = S.wx?.current || {};
  $("gAqi").textContent = a.us_aqi != null ? Math.round(a.us_aqi) : "—";
  const arc = $("gaugeArc");
  const frac = clamp((a.us_aqi ?? 0) / 300, 0, 1);
  arc.style.strokeDashoffset = 314 * (1 - frac);
  arc.style.stroke = aqiColor(a.us_aqi);
  $("vPm").textContent = fmt(a.pm2_5, 1) + " µg/m³";
  $("vPm10").textContent = fmt(a.pm10, 1) + " µg/m³";
  $("vAod").textContent = fmt(a.aerosol_optical_depth, 2);
  $("vTemp").textContent = fmt(w.temperature_2m, 1) + " °C";
  $("vRh").textContent = fmt(w.relative_humidity_2m, 0) + " %";
  $("vPress").textContent = fmt(w.surface_pressure, 0) + " hPa";
  $("vWind").textContent = fmt(w.wind_speed_10m, 0) + " KM/H";
  $("vVector").textContent = w.wind_direction_10m != null
    ? `${fmt(w.wind_direction_10m, 0)}° ${compass16(w.wind_direction_10m)} → ${compass16((w.wind_direction_10m + 180) % 360)}` : "—";
  $("vGust").textContent = fmt(w.wind_gusts_10m, 0) + " KM/H";
  if (w.wind_direction_10m != null)
    $("windNeedle").style.transform = `rotate(${(w.wind_direction_10m + 180) % 360}deg)`;
  renderSpark();
}

function renderSpark() {
  const c = $("spark"), ctx = c.getContext("2d");
  const W = c.clientWidth || 280, H = 70;
  const dpr = window.devicePixelRatio || 1;
  c.width = W * dpr; c.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  const h = S.air?.hourly;
  if (!h?.pm2_5) { ctx.fillStyle = "#5f7396"; ctx.font = "10px 'IBM Plex Mono'"; ctx.fillText("NO FORECAST", 6, 20); return; }
  const nowIdx = Math.max(0, h.time.findIndex(t => Date.parse(t) > Date.now()) - 1);
  const vals = h.pm2_5.slice(nowIdx, nowIdx + 72).filter(v => v != null);
  const max = Math.max(...vals, 10) * 1.1;
  // EPA band underlays
  for (const [lim, col] of [[9, "#38e6a1"], [35.4, "#ffd454"], [55.4, "#ffb454"], [125.4, "#ff4655"]]) {
    const y = H - (lim / max) * H;
    if (y > 0 && y < H) { ctx.strokeStyle = col + "26"; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  }
  ctx.strokeStyle = "#2ee6ff"; ctx.lineWidth = 1.4; ctx.beginPath();
  vals.forEach((v, i) => {
    const x = (i / (vals.length - 1)) * W, y = H - (v / max) * H;
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.stroke();
  ctx.fillStyle = "#5f7396"; ctx.font = "8px 'IBM Plex Mono'";
  ctx.fillText("NOW", 2, H - 2); ctx.fillText("+72H", W - 26, H - 2);
  ctx.fillText(`PEAK ${fmt(Math.max(...vals), 1)}`, 2, 9);
}

function renderAti() {
  const a = S.air?.current || {}, w = S.wx?.current || {};
  const airPts = a.us_aqi != null ? clamp(a.us_aqi, 0, 300) / 300 * 40 : 0;
  let trendPts = 0;
  const h = S.air?.hourly;
  if (h?.pm2_5 && a.pm2_5 != null) {
    const nowIdx = Math.max(0, h.time.findIndex(t => Date.parse(t) > Date.now()) - 1);
    const nxt = h.pm2_5.slice(nowIdx + 1, nowIdx + 13).filter(v => v != null);
    if (nxt.length) trendPts = clamp((Math.max(...nxt) - a.pm2_5) / Math.max(a.pm2_5, 1), 0, 1) * 10;
  }
  let firePts = 0;
  if (w.wind_direction_10m != null) {
    for (const f of S.fires) {
      const diff = angleDiff(w.wind_direction_10m, f.brg);
      if (diff <= 45) {
        firePts = Math.max(firePts, (1 - f.dist / FIRE_RANGE_KM) * Math.min(1, (w.wind_speed_10m || 0) / 30) * 15 * (1 - diff / 45 * 0.5));
      }
    }
  }
  const total = Math.round(clamp((airPts + trendPts + firePts) / 65 * 100, 0, 100));
  $("atiVal").textContent = total;
  $("atiFill").style.width = total + "%";
  $("atiParts").textContent = `air ${airPts.toFixed(1)} · trend ${trendPts.toFixed(1)} · upwind ${firePts.toFixed(1)} → scaled /65 — same math as the instrument, no personal factors`;
}

function renderFireList() {
  const host = $("fireList");
  const wdir = S.wx?.current?.wind_direction_10m;
  $("sigFires").textContent = S.fires.length;
  const upCount = wdir != null ? S.fires.filter(f => angleDiff(wdir, f.brg) <= 45).length : 0;
  $("sigUpwind").textContent = upCount;
  if (!S.fires.length) { host.innerHTML = '<div class="empty-note">NO OPEN EONET EVENTS IN RANGE</div>'; return; }
  host.innerHTML = S.fires.slice(0, 40).map(f => {
    const up = wdir != null && angleDiff(wdir, f.brg) <= 45;
    return `<div class="fire-row${up ? " upwind" : ""}" data-id="${f.id}" role="button" tabindex="0">
      <span class="fr-ico">${up ? "▲" : "●"}</span>
      <span>
        <span class="fr-name">${f.title}</span><br/>
        <span class="fr-meta">BRG ${fmt(f.brg, 0)}° ${compass16(f.brg)}${up ? " · UPWIND" : ""}</span>
      </span>
      <span class="fr-rng">${fmt(f.dist, 0)}<br/>KM</span>
    </div>`;
  }).join("");
  host.querySelectorAll(".fire-row").forEach(row => {
    const go = () => { const f = S.fires.find(x => x.id === row.dataset.id); if (f) { lockFire(f); S.map.flyTo([f.lat, f.lon], 7, { duration: 1.2 }); } };
    row.addEventListener("click", go);
    row.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
  });
}

function renderAlerts(feats) {
  const host = $("alertList");
  if (feats == null) { host.innerHTML = '<div class="empty-note">ALERT WIRE UNAVAILABLE</div>'; $("sigAlerts").textContent = "—"; return; }
  $("sigAlerts").textContent = feats.length;
  if (!feats.length) { host.innerHTML = '<div class="empty-note">NO ACTIVE FIRE/AIR PRODUCTS</div>'; return; }
  host.innerHTML = feats.slice(0, 30).map(f => {
    const p = f.properties;
    const aq = /air quality|smoke/i.test(p.event);
    return `<div class="alert-row${aq ? " aq" : ""}">
      <div class="al-ev">${p.event.toUpperCase()}</div>
      <div class="al-area">${(p.areaDesc || "").slice(0, 90)}</div>
    </div>`;
  }).join("");
}

function renderWire(arts) {
  const host = $("wire");
  if (arts == null) {
    host.innerHTML = '<div class="empty-note">GDELT WIRE UNAVAILABLE — AUTO-RETRY SCHEDULED. FEEDS: MET ✓ CAMS ✓ EONET ✓ NWS ✓</div>';
    $("sigWire").textContent = "—";
    return;
  }
  $("sigWire").textContent = arts.length;
  const seen = new Set();
  const unique = arts.filter(a => { if (seen.has(a.title)) return false; seen.add(a.title); return true; });
  host.innerHTML = unique.map(a => {
    const t = a.seendate ? `${a.seendate.slice(9, 11)}:${a.seendate.slice(11, 13)}Z` : "";
    return `<a class="wire-card" href="${a.url}" target="_blank" rel="noopener noreferrer">
      ${a.socialimage ? `<div class="wc-img" style="background-image:url('${a.socialimage}')"></div>` : ""}
      <div class="wc-body">
        <span class="wc-title">${a.title}</span>
        <span class="wc-meta"><b>${a.domain || "?"}</b> · ${a.sourcecountry || ""} · ${t}</span>
      </div>
    </a>`;
  }).join("");
  // ticker
  $("tickerInner").textContent = unique.slice(0, 12).map(a => `▸ ${a.title} [${a.domain}]`).join("   ");
}

/* ---------------- broadcast monitor ---------------- */
function initBroadcast() {
  const host = $("castChannels");
  host.innerHTML = CHANNELS.map(c => `<button class="cast-btn" data-ch="${c.id}">${c.name}</button>`).join("")
    + `<a class="cast-btn" href="https://www.youtube.com/results?search_query=wildfire+live" target="_blank" rel="noopener noreferrer">SEARCH LIVE ↗</a>`;
  host.querySelectorAll("[data-ch]").forEach(btn => btn.addEventListener("click", () => {
    host.querySelectorAll(".cast-btn").forEach(b => b.classList.remove("on"));
    btn.classList.add("on");
    const stage = $("castStage");
    stage.innerHTML = `<iframe
      src="https://www.youtube.com/embed/live_stream?channel=${btn.dataset.ch}&autoplay=1&mute=1"
      title="Live broadcast — ${btn.textContent}"
      allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen
      referrerpolicy="strict-origin-when-cross-origin"></iframe>`;
    log(`BROADCAST MONITOR — ${btn.textContent} LIVE STREAM OPENED`, "ok");
  }));
}

/* ---------------- AOI + controls ---------------- */
function setAoi(lat, lon, why) {
  S.aoi = { lat, lon };
  drawAoiMarker(); drawRings();
  if (S.layers.lock) { S.map.removeLayer(S.layers.lock); S.layers.lock = null; $("lockinfo").hidden = true; }
  S.map.flyTo([lat, lon], Math.max(S.map.getZoom(), 5), { duration: 1 });
  log(`${why} — ${lat.toFixed(4)}, ${lon.toFixed(4)} · RESAMPLING ALL FEEDS`, "warn");
  fetchCore(); fetchWindGrid(); fetchAqiGrid(); fetchFires(); fetchAlerts();
}

function toggleAoiMode(force) {
  S.aoiMode = force != null ? force : !S.aoiMode;
  $("btnAoi").classList.toggle("active", S.aoiMode);
  $("btnAoi").textContent = S.aoiMode ? "CLICK MAP…" : "REPOSITION AOI";
}

function initControls() {
  $("btnAoi").addEventListener("click", () => toggleAoiMode());
  $("btnGeo").addEventListener("click", () => {
    if (!navigator.geolocation) { log("GEOLOCATION UNSUPPORTED", "err"); return; }
    log("REQUESTING DEVICE POSITION…");
    navigator.geolocation.getCurrentPosition(
      (pos) => setAoi(pos.coords.latitude, pos.coords.longitude, "GEOLOCATED AOI"),
      (err) => log("GEOLOCATION DENIED — " + err.message.toUpperCase(), "err"),
      { timeout: 12000, maximumAge: 300000 }
    );
  });
  document.querySelectorAll(".lbtn").forEach(btn => btn.addEventListener("click", () => {
    const k = btn.dataset.layer;
    S.show[k] = !S.show[k];
    btn.classList.toggle("on", S.show[k]);
    if (k === "fires") drawFires();
    if (k === "rings") drawRings();
    if (k === "plume") drawPlume();
    if (k === "aqi") { if (S.show.aqi) fetchAqiGrid(); else drawAqiGrid(null); }
    if (k === "wind") { clearWindCanvas(); if (S.show.wind && REDUCED) drawStaticArrows(); }
    log(`LAYER ${k.toUpperCase()} ${S.show[k] ? "ENABLED" : "DISABLED"}`);
  }));
  window.addEventListener("resize", () => { sizeCanvas(); seedParticles(); });
}

/* ---------------- boot ---------------- */
function boot() {
  startClocks();
  initMap();
  sizeCanvas();
  initControls();
  initBroadcast();
  drawRings();
  log("AEGIS COMMAND CONSOLE ONLINE", "ok");
  log("ACQUIRING SIGNALS — MET · CAMS · WINDFIELD · EONET · NWS · GDELT");

  fetchCore();
  fetchWindGrid();
  fetchAqiGrid();
  fetchFires();
  fetchAlerts();
  setTimeout(fetchWire, 1200); // stagger GDELT (strict rate limit)

  if (!REDUCED) stepParticles();

  // refresh cadence
  S.timers.push(setInterval(fetchCore, 5 * 60e3));
  S.timers.push(setInterval(fetchWindGrid, 10 * 60e3));
  S.timers.push(setInterval(fetchAqiGrid, 10 * 60e3));
  S.timers.push(setInterval(fetchFires, 10 * 60e3));
  S.timers.push(setInterval(fetchAlerts, 5 * 60e3));
  S.timers.push(setInterval(fetchWire, 5 * 60e3));
}

boot();
