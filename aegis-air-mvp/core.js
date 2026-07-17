"use strict";
/* ============================================================
   AEGIS AIR // FIELD INTEL — core orchestrator.
   Local-first: all personal data in localStorage. No backend.
   ============================================================ */

const DEFAULT_LOC = { lat: 42.9656, lon: -78.8703, label: "BUFFALO/KENMORE (DEFAULT)" };
const FIRE_RANGE_KM = 2600;
const LS = { profile: "aegis.profile.v1", checkins: "aegis.checkins.v1", location: "aegis.location.v1", events: "aegis.events.v1" };
const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const SENSITIVITY_FACTORS = [
  ["asthma", "ASTHMA"], ["copd", "COPD / CHRONIC LUNG DISEASE"], ["heart", "HEART / VASCULAR CONDITION"],
  ["pregnant", "PREGNANT"], ["age", "CHILD (<18) OR OLDER ADULT (65+)"],
  ["outdoorWork", "OUTDOOR WORK / EXERCISE MOST DAYS"], ["smokeSensitive", "PAST STRONG SMOKE REACTIONS"],
];
const SYMPTOMS = [
  ["cough", "COUGH"], ["wheeze", "WHEEZE"], ["sob", "SHORTNESS OF BREATH (ACTIVITY)"],
  ["chestTight", "CHEST TIGHTNESS"], ["throat", "THROAT / EYE IRRITATION"],
  ["headache", "HEADACHE"], ["fatigue", "UNUSUAL FATIGUE"],
];
const EMERGENCY_SYMPTOMS = [
  ["sobRest", "SEVERE BREATHLESSNESS AT REST"], ["chestPain", "CHEST PAIN OR PRESSURE"],
  ["blueLips", "BLUISH LIPS OR FACE"], ["confusion", "CONFUSION OR FAINTING"],
];

const A = {
  loc: loadJSON(LS.location) || { ...DEFAULT_LOC },
  wx: null, air: null,
  fires: [], clusters: [],
  nowcast: null, sentinel: null, personal: null,
  events: loadJSON(LS.events) || [],
  timers: [],
};

/* ---------- utils ---------- */
function $(id) { return document.getElementById(id); }
function loadJSON(k) { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } }
function saveJSON(k, v) { localStorage.setItem(k, JSON.stringify(v)); }
function fmt(n, d = 0) { return (n == null || Number.isNaN(n)) ? "—" : Number(n).toFixed(d); }
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
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
const angleDiff = (x, y) => { const d = Math.abs(x - y) % 360; return d > 180 ? 360 - d : d; };
const compass16 = (deg) => deg == null ? "—" :
  ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"][Math.round(deg / 22.5) % 16];
function aqiColor(v) {
  if (v == null) return "#5f7396";
  if (v <= 50) return "#38e6a1"; if (v <= 100) return "#ffd454"; if (v <= 150) return "#ffb454";
  if (v <= 200) return "#ff4655"; if (v <= 300) return "#8f7bff"; return "#c96bff";
}
function aqiName(v) {
  if (v == null) return "—";
  if (v <= 50) return "GOOD"; if (v <= 100) return "MODERATE"; if (v <= 150) return "USG";
  if (v <= 200) return "UNHEALTHY"; if (v <= 300) return "VERY UNHEALTHY"; return "HAZARDOUS";
}
let toastTimer;
function toast(msg) {
  const el = $("toast"); el.textContent = msg; el.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove("show"), 2600);
}
function srcStatus(k, ok) {
  const el = document.querySelector(`#srcRow [data-src="${k}"]`);
  if (el) el.className = ok ? "ok" : "err";
}
function logIntelEvent(kind, msg, cls = "") {
  A.events.unshift({ ts: new Date().toISOString(), kind, msg, cls });
  A.events = A.events.slice(0, 120);
  saveJSON(LS.events, A.events);
  renderEvents();
}

/* ---------- boot sequence ---------- */
const BOOT_LINES = [
  "INIT FIELD INSTRUMENT v2.0",
  "LOADING LOCAL ARCHIVE ................ <ok>OK</ok>",
  "MET / CAMS UPLINK .................... <ok>OK</ok>",
  "EONET FIRE CATALOG ................... <ok>OK</ok>",
  "GIBS ORBITAL IMAGERY ................. <ok>OK</ok>",
  "NEURAL CORES (ON-DEVICE) ............. <ok>ARMED</ok>",
];
function bootSequence() {
  const host = $("bootLog");
  if (REDUCED) { $("bootScreen").classList.add("done"); return; }
  let i = 0;
  const next = () => {
    if (i >= BOOT_LINES.length) { setTimeout(() => $("bootScreen").classList.add("done"), 320); return; }
    const div = document.createElement("div");
    div.innerHTML = BOOT_LINES[i].replace("<ok>", '<span class="ok">').replace("</ok>", "</span>");
    host.appendChild(div);
    i++; setTimeout(next, 170);
  };
  next();
}

/* ---------- clock ---------- */
function startClock() {
  const tick = () => { $("zChip").textContent = "Z " + new Date().toISOString().slice(11, 19); };
  tick(); A.timers.push(setInterval(tick, 1000));
}

/* ---------- data ---------- */
async function fetchAll() {
  const { lat, lon } = A.loc;
  $("btnRefresh").classList.add("spin");
  const wxUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m&timezone=auto`;
  const aqUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&current=us_aqi,pm2_5,pm10,aerosol_optical_depth&hourly=pm2_5,us_aqi&past_days=7&forecast_days=4&timezone=auto`;
  const fireUrl = "https://eonet.gsfc.nasa.gov/api/v3/events?category=wildfires&status=open&limit=800";

  const [wx, aq, fires] = await Promise.allSettled([
    fetch(wxUrl).then(r => r.json()),
    fetch(aqUrl).then(r => r.json()),
    fetch(fireUrl).then(r => r.json()),
  ]);
  if (wx.status === "fulfilled") { A.wx = wx.value; srcStatus("wx", true); } else srcStatus("wx", false);
  if (aq.status === "fulfilled") { A.air = aq.value; srcStatus("aq", true); } else srcStatus("aq", false);
  if (fires.status === "fulfilled") { ingestFires(fires.value); srcStatus("eonet", true); } else srcStatus("eonet", false);

  $("btnRefresh").classList.remove("spin");
  runModels();
  renderAll();
}

function ingestFires(eonet) {
  const { lat, lon } = A.loc;
  const out = [];
  for (const ev of eonet.events || []) {
    const g = (ev.geometry || []).slice(-1)[0];
    if (!g) continue;
    let la, lo;
    if (g.type === "Point") [lo, la] = g.coordinates;
    else if (g.type === "Polygon") [lo, la] = g.coordinates[0][0];
    else continue;
    const dist = haversineKm(lat, lon, la, lo);
    if (dist > FIRE_RANGE_KM) continue;
    out.push({ id: ev.id, title: ev.title, date: g.date, lat: la, lon: lo, dist, brg: bearingDeg(lat, lon, la, lo) });
  }
  out.sort((a, b) => a.dist - b.dist);
  A.fires = out;
  A.clusters = AegisML.kmeansFires(out);
  AegisSat.redrawFires();
}

/* ---------- ML orchestration ---------- */
function nowIdx() {
  const t = A.air?.hourly?.time;
  if (!t) return -1;
  const i = t.findIndex(x => Date.parse(x) > Date.now());
  return Math.max(0, i - 1);
}

function runModels() {
  const h = A.air?.hourly;
  if (!h?.pm2_5) { srcStatus("ml", false); return; }
  const idx = nowIdx();
  const histT = h.time.slice(0, idx + 1), histV = h.pm2_5.slice(0, idx + 1);

  try {
    A.nowcast = AegisML.trainNowcast(histT, histV);
    A.sentinel = AegisML.sentinel(histT, histV, A.air?.current?.pm2_5);
    const prof = getProfile();
    A.personal = AegisML.trainPersonal(getCheckins(), prof.hrBaseline);
    srcStatus("ml", true);

    if (A.sentinel && Math.abs(A.sentinel.z) >= 2) {
      const last = A.events[0];
      const msg = `PM2.5 ANOMALY — ${fmt(A.air.current.pm2_5, 1)} µg/m³ IS ${fmt(A.sentinel.z, 1)}σ VS 7-DAY SAME-HOUR BASELINE (${fmt(A.sentinel.median, 1)})`;
      if (!last || last.msg !== msg) logIntelEvent("anomaly", msg, A.sentinel.z > 0 ? "bad" : "warn");
    }
  } catch { srcStatus("ml", false); }
}

/* ---------- score (same transparent formula as v1) ---------- */
function getProfile() { return loadJSON(LS.profile) || { factors: {}, hrBaseline: null }; }
function getCheckins() { return loadJSON(LS.checkins) || []; }
function latestCheckinWithin(hours) {
  const cutoff = Date.now() - hours * 3600e3;
  return getCheckins().find(c => Date.parse(c.ts) >= cutoff) || null;
}

function computeScore() {
  const p = getProfile();
  const cur = A.air?.current || {}, wind = A.wx?.current || {};
  const aqi = cur.us_aqi ?? null, pm = cur.pm2_5 ?? null;
  const rows = []; let emergencyActive = false;

  const airPts = aqi == null ? 0 : clamp(aqi, 0, 300) / 300 * 40;
  rows.push(["AIR BURDEN", aqi == null ? "AQI unavailable" : `US AQI ${Math.round(aqi)} (${aqiName(aqi)}) · PM2.5 ${fmt(pm, 1)}`, "+" + fmt(airPts, 1)]);

  let trendPts = 0, trendBasis = "forecast unavailable";
  const h = A.air?.hourly, idx = nowIdx();
  if (h && pm != null && idx >= 0) {
    const next12 = h.pm2_5.slice(idx + 1, idx + 13).filter(v => v != null);
    if (next12.length) {
      const peak = Math.max(...next12), rise = (peak - pm) / Math.max(pm, 1);
      trendPts = clamp(rise, 0, 1) * 10;
      trendBasis = `12 h peak ${fmt(peak, 1)} vs now ${fmt(pm, 1)}`;
    }
  }
  rows.push(["RISING-SMOKE TREND", trendBasis, "+" + fmt(trendPts, 1)]);

  let firePts = 0, fireBasis = "no upwind events";
  if (wind.wind_direction_10m != null) {
    for (const f of A.fires) {
      const diff = angleDiff(wind.wind_direction_10m, f.brg);
      if (diff <= 45) {
        const pts = (1 - f.dist / FIRE_RANGE_KM) * Math.min(1, (wind.wind_speed_10m || 0) / 30) * 15 * (1 - diff / 45 * 0.5);
        if (pts > firePts) { firePts = pts; fireBasis = `wind ${compass16(wind.wind_direction_10m)} ≈ ${f.title.slice(0, 30)} @ ${fmt(f.dist, 0)} km`; }
      }
    }
  }
  rows.push(["UPWIND FIRE", fireBasis, "+" + fmt(firePts, 1)]);

  const nF = Object.values(p.factors || {}).filter(Boolean).length;
  const mult = Math.min(1.6, 1 + 0.15 * nF);
  rows.push(["SENSITIVITY", `${nF} profile factor(s)`, "×" + mult.toFixed(2)]);

  const ci = latestCheckinWithin(24);
  let symPts = 0, symBasis = "no check-in / 24 h";
  if (ci) {
    if (ci.emergency?.length) emergencyActive = true;
    symPts = Math.min(20, (ci.symptoms?.length || 0) * 4);
    symBasis = `${ci.symptoms?.length || 0} symptom(s) logged`;
  }
  rows.push(["RECENT SYMPTOMS", symBasis, "+" + fmt(symPts, 1)]);

  let hrPts = 0, hrBasis = "no HR / baseline pair";
  if (ci?.hr && p.hrBaseline) {
    const dev = (ci.hr - p.hrBaseline) / p.hrBaseline;
    if (dev > 0.10) hrPts = Math.min(10, (dev - 0.10) * 100);
    hrBasis = `HR ${ci.hr} vs ${p.hrBaseline} (${dev > 0 ? "+" : ""}${fmt(dev * 100, 0)}%)`;
  }
  rows.push(["HR DEVIATION", hrBasis + (ci?.spo2 ? ` · SpO₂ ${ci.spo2}% recorded, never scored` : ""), "+" + fmt(hrPts, 1)]);

  let outPts = 0, outBasis = "no outdoor time logged";
  if (ci?.outdoorMin != null) {
    const w = (aqi != null && aqi > 100) ? 2 : 1;
    outPts = Math.min(5, ci.outdoorMin / 240 * 5 * w);
    outBasis = `${ci.outdoorMin} min` + (w > 1 ? " · AQI>100 ×2" : "");
  }
  rows.push(["OUTDOOR EXPOSURE", outBasis, "+" + fmt(outPts, 1)]);

  const total = Math.round(clamp((airPts + trendPts + firePts) * mult + symPts + hrPts + outPts, 0, 100));
  return { rows, total, emergencyActive };
}
function scoreCat(t) {
  if (t < 20) return { name: "LOW", color: "#38e6a1", msg: "Normal activities are reasonable for you today." };
  if (t < 40) return { name: "MODERATE", color: "#ffd454", msg: "Consider shorter or lighter outdoor exertion." };
  if (t < 60) return { name: "ELEVATED", color: "#ffb454", msg: "Limit prolonged outdoor exertion; keep reliever medication close if prescribed." };
  if (t < 80) return { name: "HIGH", color: "#ff4655", msg: "Prefer filtered indoor air; use a fitted N95 outdoors." };
  return { name: "VERY HIGH", color: "#c96bff", msg: "Avoid outdoor exposure. If symptoms worsen, contact a clinician." };
}

/* ---------- renderers ---------- */
function renderAll() {
  renderTelemetry(); renderScore(); renderSentinel(); renderFires();
  renderNeural(); renderBriefing(); renderTimeline(); renderHistory(); renderEvents();
}

function renderTelemetry() {
  const c = A.air?.current || {}, w = A.wx?.current || {};
  $("vAqi").textContent = c.us_aqi != null ? Math.round(c.us_aqi) : "—";
  $("aqiBadge").innerHTML = c.us_aqi != null ? `<span class="aqi-chip" style="background:${aqiColor(c.us_aqi)}">${aqiName(c.us_aqi)}</span>` : "";
  $("vPm").textContent = fmt(c.pm2_5, 1) + " µg/m³";
  $("vAod").textContent = fmt(c.aerosol_optical_depth, 2);
  $("vWind").textContent = w.wind_speed_10m != null ? `${fmt(w.wind_speed_10m, 0)} ${compass16(w.wind_direction_10m)}` : "—";
  $("vTemp").textContent = fmt(w.temperature_2m, 1) + " °C";
  $("vRh").textContent = fmt(w.relative_humidity_2m, 0) + " %";
}

function renderScore() {
  const s = computeScore();
  const tbody = $("compTable").querySelector("tbody");
  tbody.innerHTML = s.rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td></tr>`).join("")
    + `<tr class="total"><td>TOTAL</td><td>(air+trend+fire)×sens + symptoms + HR + outdoor · cap 100</td><td>${s.emergencyActive ? "—" : s.total}</td></tr>`;
  const arc = $("scoreArc");
  if (s.emergencyActive) {
    $("scoreNum").textContent = "—";
    $("scoreCat").textContent = "EMERGENCY REPORTED";
    $("scoreCat").style.color = "#ff4655";
    $("scoreMsg").textContent = "No score while emergency-level symptoms are active. Seek medical care.";
    arc.style.stroke = "#ff4655"; arc.style.strokeDashoffset = 0;
    return;
  }
  const cat = scoreCat(s.total);
  $("scoreNum").textContent = s.total;
  $("scoreCat").textContent = cat.name;
  $("scoreCat").style.color = cat.color;
  $("scoreMsg").textContent = cat.msg;
  arc.style.stroke = cat.color;
  arc.style.strokeDashoffset = 314 * (1 - s.total / 100);
}

function renderSentinel() {
  const st = $("sentState"), det = $("sentDetail");
  if (!A.sentinel) { st.textContent = "STANDBY"; st.className = "sent-state"; det.textContent = "insufficient baseline history"; return; }
  const z = A.sentinel.z;
  if (z >= 2) { st.textContent = "ANOMALY"; st.className = "sent-state bad"; }
  else if (z >= 1) { st.textContent = "WATCH"; st.className = "sent-state warn"; }
  else { st.textContent = "NOMINAL"; st.className = "sent-state ok"; }
  det.textContent = `current PM2.5 is ${fmt(z, 1)}σ vs the same-hour 7-day baseline (median ${fmt(A.sentinel.median, 1)} µg/m³, n=${A.sentinel.n})`;
}

function renderFires() {
  $("vFires").textContent = A.fires.length;
  const wdir = A.wx?.current?.wind_direction_10m;
  const up = wdir != null ? A.fires.filter(f => angleDiff(wdir, f.brg) <= 45) : [];
  $("vUpwind").textContent = wdir != null ? up.length : "—";
  const n = A.fires[0];
  $("vNearest").textContent = n ? `${n.title} · ${fmt(n.dist, 0)} KM ${compass16(n.brg)}` : "NONE IN RANGE";
  $("clusterList").innerHTML = A.clusters.map((c, i) => {
    const d = haversineKm(A.loc.lat, A.loc.lon, c.lat, c.lon);
    return `<span class="cluster">CLUSTER ${String.fromCharCode(65 + i)} — <b>${c.count}</b> EVENTS · ${fmt(d, 0)} KM ${compass16(bearingDeg(A.loc.lat, A.loc.lon, c.lat, c.lon))}</span>`;
  }).join("") || '<span class="empty-note">k-means requires ≥6 events in range</span>';
}

function renderNeural() {
  // nowcast
  if (A.nowcast) {
    $("ncStatus").textContent = "TRAINED";
    $("ncRmse").textContent = fmt(A.nowcast.rmse, 2) + " µg/m³";
    $("ncPeak").textContent = fmt(Math.max(...A.nowcast.forecast), 1) + " µg/m³";
    $("ncWeights").textContent = A.nowcast.featNames.map((f, i) => `${f.padEnd(10)} ${A.nowcast.weights[i] >= 0 ? "+" : ""}${A.nowcast.weights[i].toFixed(3)}`).join("\n");
  } else {
    $("ncStatus").textContent = "INSUFFICIENT HISTORY";
    $("ncWeights").textContent = "—";
  }
  // sentinel numbers
  $("azScore").textContent = A.sentinel ? fmt(A.sentinel.z, 2) + "σ" : "—";
  $("azBase").textContent = A.sentinel ? fmt(A.sentinel.median, 1) + " µg/m³" : "—";
  // personal
  const p = A.personal;
  if (!p) { $("pplStatus").textContent = "—"; return; }
  if (p.trained) {
    $("pplStatus").textContent = "TRAINED";
    $("pplN").textContent = `${p.n} ENTRIES (${p.pos} SYMPTOMATIC)`;
    $("pplAcc").textContent = fmt(p.acc * 100, 0) + " %";
    $("pplWeights").textContent = p.featNames.map((f, i) => `${f.padEnd(13)} ${p.weights[i] >= 0 ? "+" : ""}${p.weights[i].toFixed(3)}  ${i > 0 ? (p.weights[i] > 0.15 ? "▲ ASSOCIATED" : p.weights[i] < -0.15 ? "▼ INVERSE" : "· WEAK") : ""}`).join("\n");
    $("pplProgress").style.width = "100%";
  } else {
    $("pplStatus").textContent = "COLLECTING DATA";
    $("pplN").textContent = `${p.n} / 8 MINIMUM` + (p.pos === 0 && p.n > 0 ? " · NEEDS SYMPTOMATIC + CLEAR DAYS" : "");
    $("pplAcc").textContent = "—";
    $("pplWeights").textContent = "MODEL LOCKED — LOG VARIED CHECK-INS (BOTH GOOD AND BAD DAYS) TO UNLOCK.";
    $("pplProgress").style.width = clamp(p.n / 8 * 100, 4, 96) + "%";
  }
}

function renderBriefing() {
  const c = A.air?.current || {}, w = A.wx?.current || {};
  const s = computeScore();
  const cat = scoreCat(s.total);
  const wdir = w.wind_direction_10m;
  const up = wdir != null ? A.fires.filter(f => angleDiff(wdir, f.brg) <= 45) : [];
  const anomaly = A.sentinel && A.sentinel.z >= 2;
  const ncPeak = A.nowcast ? Math.max(...A.nowcast.forecast) : null;
  const rising = ncPeak != null && c.pm2_5 != null && ncPeak > c.pm2_5 * 1.3;

  const lines = [];
  lines.push(`<span class="t">SITREP ${new Date().toISOString().slice(0, 16).replace("T", " ")}Z · AUTO-COMPILED FROM LIVE SIGNALS</span>`);
  lines.push(`AIR: US AQI <span class="${c.us_aqi > 100 ? "hl" : "ok"}">${c.us_aqi != null ? Math.round(c.us_aqi) : "—"} ${aqiName(c.us_aqi)}</span> · PM2.5 ${fmt(c.pm2_5, 1)} µg/m³${anomaly ? ' · <span class="bad">SENTINEL FLAGS ANOMALY VS 7-DAY NORM</span>' : ""}.`);
  lines.push(`WIND: ${fmt(w.wind_speed_10m, 0)} km/h FROM ${compass16(wdir)} — ${up.length ? `<span class="hl">${up.length} FIRE EVENT(S) IN YOUR UPWIND SECTOR, CLOSEST ${fmt(up[0]?.dist, 0)} KM</span>` : '<span class="ok">UPWIND SECTOR CLEAR</span>'}.`);
  if (ncPeak != null) lines.push(`NEURAL NOWCAST: 24 h peak ≈ ${fmt(ncPeak, 1)} µg/m³ ${rising ? '<span class="hl">— RISING PATTERN</span>' : "— steady"} (on-device model, RMSE ${fmt(A.nowcast.rmse, 1)}).`);
  lines.push(`POSTURE: <span style="color:${cat.color}">${cat.name} (${s.emergencyActive ? "—" : s.total}/100)</span> — ${cat.msg}`);
  lines.push(`<span class="t">RULE-ENGINE OUTPUT ON MODELED DATA · NOT MEDICAL ADVICE</span>`);
  $("briefing").innerHTML = lines.join("<br/>");
}

/* ---------- timeline chart: 7d history + CAMS + nowcast ---------- */
function renderTimeline() {
  const cv = $("timeline"), ctx = cv.getContext("2d");
  const W = cv.clientWidth || cv.parentElement.clientWidth - 24, H = 240;
  const dpr = window.devicePixelRatio || 1;
  cv.width = W * dpr; cv.height = H * dpr; cv.style.height = H + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  const h = A.air?.hourly;
  ctx.font = "9px 'IBM Plex Mono'"; ctx.fillStyle = "#5f7396";
  if (!h?.pm2_5) { ctx.fillText("NO SIGNAL", 10, 24); return; }

  const idx = nowIdx();
  const histV = h.pm2_5.slice(0, idx + 1);
  const futV = h.pm2_5.slice(idx + 1, idx + 73);
  const nc = A.nowcast?.forecast || [];
  const all = [...histV, ...futV, ...nc].filter(v => v != null);
  const vMax = Math.max(...all, 10) * 1.12;
  const total = histV.length + Math.max(futV.length, nc.length);
  const x = (i) => i / (total - 1) * (W - 46) + 38;
  const y = (v) => 14 + (1 - v / vMax) * (H - 44);

  // EPA bands
  for (const [lim, col] of [[9, "#38e6a1"], [35.4, "#ffd454"], [55.4, "#ffb454"], [125.4, "#ff4655"]]) {
    if (lim > vMax) continue;
    ctx.strokeStyle = col + "22"; ctx.beginPath(); ctx.moveTo(38, y(lim)); ctx.lineTo(W - 8, y(lim)); ctx.stroke();
    ctx.fillStyle = col + "66"; ctx.fillText(lim, 8, y(lim) + 3);
  }
  // day boundaries
  ctx.textAlign = "center";
  for (let i = 0; i < h.time.length && i < total; i++) {
    const d = new Date(h.time[i]);
    if (d.getHours() === 0) {
      ctx.strokeStyle = "#16233c66"; ctx.beginPath(); ctx.moveTo(x(i), 14); ctx.lineTo(x(i), H - 30); ctx.stroke();
      ctx.fillStyle = "#3d5170"; ctx.fillText(d.toLocaleDateString(undefined, { weekday: "narrow" }), x(i), H - 18);
    }
  }
  // anomaly markers on history (z>=2 approximation: > p95)
  const sorted = [...histV].filter(v => v != null).sort((a, b) => a - b);
  const p95 = sorted[Math.floor(sorted.length * 0.95)] ?? Infinity;

  // history line
  ctx.strokeStyle = "#2ee6ff"; ctx.lineWidth = 1.4; ctx.beginPath();
  histV.forEach((v, i) => { if (v == null) return; i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v)); });
  ctx.stroke();
  histV.forEach((v, i) => {
    if (v == null || v < p95 || v < 15) return;
    ctx.fillStyle = "#ff4655"; ctx.beginPath(); ctx.arc(x(i), y(v), 2.2, 0, Math.PI * 2); ctx.fill();
  });
  // CAMS future
  ctx.strokeStyle = "#8f7bff"; ctx.setLineDash([4, 3]); ctx.beginPath();
  futV.forEach((v, i) => { if (v == null) return; i ? ctx.lineTo(x(histV.length + i), y(v)) : ctx.moveTo(x(histV.length + i), y(v)); });
  ctx.stroke(); ctx.setLineDash([]);
  // nowcast
  if (nc.length) {
    ctx.strokeStyle = "#ffb454"; ctx.setLineDash([2, 3]); ctx.beginPath();
    nc.forEach((v, i) => { i ? ctx.lineTo(x(histV.length + i), y(v)) : ctx.moveTo(x(histV.length + i), y(v)); });
    ctx.stroke(); ctx.setLineDash([]);
  }
  // NOW marker
  ctx.strokeStyle = "#d7e4f7"; ctx.setLineDash([3, 3]);
  ctx.beginPath(); ctx.moveTo(x(histV.length - 1), 14); ctx.lineTo(x(histV.length - 1), H - 30); ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = "#93a4c4"; ctx.fillText("NOW", x(histV.length - 1), H - 6);
  ctx.textAlign = "left";
  ctx.fillStyle = "#5f7396"; ctx.fillText("PM2.5 µg/m³ · 7D HISTORY + T+72H", 38, 10);
}

/* ---------- events ---------- */
function renderEvents() {
  const host = $("eventList");
  if (!host) return;
  if (!A.events.length) { host.innerHTML = '<div class="empty-note">NO DETECTED EVENTS YET — THE SENTINEL LOGS ANOMALIES HERE AS THEY OCCUR.</div>'; return; }
  host.innerHTML = A.events.slice(0, 30).map(e =>
    `<div class="event-row ${e.cls}"><span class="t">${e.ts.slice(0, 16).replace("T", " ")}Z · ${e.kind.toUpperCase()}</span><br/>${e.msg}</div>`).join("");
}

/* ---------- check-ins / profile / history ---------- */
function buildForms() {
  const p = getProfile();
  $("profileChecks").innerHTML = SENSITIVITY_FACTORS.map(([k, l]) =>
    `<label class="chk"><input type="checkbox" data-factor="${k}" ${p.factors[k] ? "checked" : ""}/> ${l}</label>`).join("");
  $("hrBaseline").value = p.hrBaseline ?? "";
  $("symptomChecks").innerHTML = SYMPTOMS.map(([k, l]) => `<label class="chk"><input type="checkbox" data-sym="${k}"/> ${l}</label>`).join("");
  $("emergencyChecks").innerHTML = EMERGENCY_SYMPTOMS.map(([k, l]) => `<label class="chk em"><input type="checkbox" data-esym="${k}"/> ${l}</label>`).join("");
}
function saveProfile() {
  const factors = {};
  document.querySelectorAll("#profileChecks input[data-factor]").forEach(cb => factors[cb.dataset.factor] = cb.checked);
  const hr = parseInt($("hrBaseline").value, 10);
  saveJSON(LS.profile, { factors, hrBaseline: Number.isFinite(hr) ? hr : null });
  toast("PROFILE SAVED LOCALLY ✓");
  runModels(); renderAll();
}
function saveCheckin() {
  const symptoms = [], emergency = [];
  document.querySelectorAll("#symptomChecks input:checked").forEach(cb => symptoms.push(cb.dataset.sym));
  document.querySelectorAll("#emergencyChecks input:checked").forEach(cb => emergency.push(cb.dataset.esym));
  const hr = parseInt($("ciHr").value, 10), spo2 = parseInt($("ciSpo2").value, 10), outdoor = parseInt($("ciOutdoor").value, 10);
  const entry = {
    ts: new Date().toISOString(), symptoms, emergency,
    hr: Number.isFinite(hr) ? hr : null, spo2: Number.isFinite(spo2) ? spo2 : null,
    outdoorMin: Number.isFinite(outdoor) ? outdoor : null,
    notes: $("ciNotes").value.trim() || null,
    context: { aqi: A.air?.current?.us_aqi ?? null, pm25: A.air?.current?.pm2_5 ?? null, lat: A.loc.lat, lon: A.loc.lon },
  };
  const list = getCheckins(); list.unshift(entry); saveJSON(LS.checkins, list.slice(0, 500));
  document.querySelectorAll("#symptomChecks input,#emergencyChecks input").forEach(cb => cb.checked = false);
  $("ciHr").value = ""; $("ciSpo2").value = ""; $("ciOutdoor").value = ""; $("ciNotes").value = "";
  toast("ENTRY LOGGED · PATTERN LEARNER UPDATED");
  logIntelEvent("checkin", `FIELD CHECK-IN — ${symptoms.length} SYMPTOM(S)${entry.hr ? ` · HR ${entry.hr}` : ""}${entry.outdoorMin != null ? ` · ${entry.outdoorMin} MIN OUTDOORS` : ""}`);
  runModels(); renderAll();
  if (emergency.length) $("emergencyOverlay").classList.add("show");
}
function renderHistory() {
  const list = getCheckins(), host = $("historyList");
  const symLabel = Object.fromEntries([...SYMPTOMS, ...EMERGENCY_SYMPTOMS]);
  if (!list.length) { host.innerHTML = '<div class="empty-note">NO ENTRIES YET.</div>'; return; }
  host.innerHTML = list.slice(0, 20).map(c => {
    const tags = [...(c.emergency || []).map(s => `<span class="em">${symLabel[s] || s}</span>`),
                  ...(c.symptoms || []).map(s => `<span>${symLabel[s] || s}</span>`)].join("");
    const vit = [c.hr ? `HR ${c.hr}` : null, c.spo2 ? `SPO₂ ${c.spo2}%` : null, c.outdoorMin != null ? `${c.outdoorMin} MIN OUT` : null].filter(Boolean).join(" · ");
    return `<div class="entry"><span class="when">${new Date(c.ts).toLocaleString()} · AQI ${c.context?.aqi != null ? Math.round(c.context.aqi) : "—"} AT LOG</span>
      <div class="tags">${tags || "<span>NO SYMPTOMS</span>"}</div>${vit ? `<div>${vit}</div>` : ""}${c.notes ? `<div style="color:var(--dim)">"${c.notes}"</div>` : ""}</div>`;
  }).join("");
}
function exportJSON() {
  const payload = {
    exportedAt: new Date().toISOString(), app: "aegis-air-field-intel-v2",
    location: A.loc, profile: getProfile(), checkins: getCheckins(), detectedEvents: A.events,
    models: {
      nowcast: A.nowcast ? { weights: A.nowcast.weights, features: A.nowcast.featNames, rmse: A.nowcast.rmse } : null,
      personal: A.personal?.trained ? { weights: A.personal.weights, features: A.personal.featNames, acc: A.personal.acc } : null,
    },
    lastEnvironment: { weather: A.wx?.current ?? null, air: A.air?.current ?? null, firesInRange: A.fires.length },
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "aegis-export-" + new Date().toISOString().slice(0, 10) + ".json";
  a.click(); URL.revokeObjectURL(a.href);
  toast("ARCHIVE EXPORTED");
}
function clearAll() {
  if (!confirm("DELETE ALL LOCALLY STORED DATA (profile, check-ins, events, location)? This cannot be undone.")) return;
  Object.values(LS).forEach(k => localStorage.removeItem(k));
  A.loc = { ...DEFAULT_LOC }; A.events = [];
  buildForms(); runModels(); renderAll(); updateWhere();
  toast("LOCAL ARCHIVE WIPED");
}

/* ---------- location ---------- */
function updateWhere() {
  $("whereChip").textContent = (A.loc.label || `${A.loc.lat.toFixed(3)}, ${A.loc.lon.toFixed(3)}`).toUpperCase();
}
function useGeolocation() {
  if (!navigator.geolocation) { toast("GEOLOCATION UNSUPPORTED"); return; }
  toast("REQUESTING POSITION…");
  navigator.geolocation.getCurrentPosition(pos => {
    A.loc = { lat: pos.coords.latitude, lon: pos.coords.longitude, label: `FIELD POS ${pos.coords.latitude.toFixed(3)}, ${pos.coords.longitude.toFixed(3)}` };
    saveJSON(LS.location, A.loc);
    updateWhere(); fetchAll();
    AegisSat.recenter(A.loc.lat, A.loc.lon);
    logIntelEvent("nav", `POSITION UPDATE — ${A.loc.lat.toFixed(4)}, ${A.loc.lon.toFixed(4)}`);
  }, err => toast("POSITION DENIED — " + err.message), { timeout: 12000, maximumAge: 300000 });
}

/* ---------- module nav ---------- */
function switchMod(name) {
  document.querySelectorAll(".mod").forEach(m => {
    const on = m.dataset.mod === name;
    m.classList.toggle("on", on); m.setAttribute("aria-selected", on);
  });
  document.querySelectorAll(".module").forEach(s => s.classList.toggle("on", s.id === "mod-" + name));
  if (name === "satrecon") {
    AegisSat.init({ center: [A.loc.lat, A.loc.lon], getFires: () => A.fires, onLog: (m, c) => logIntelEvent("sat", m, c || "") });
    srcStatus("gibs", true);
    setTimeout(AegisSat.invalidate, 60);
  }
  if (name === "signals") setTimeout(renderTimeline, 40);
}

/* ---------- wire-up & boot ---------- */
document.querySelectorAll(".mod").forEach(m => m.addEventListener("click", () => switchMod(m.dataset.mod)));
$("btnGeo").addEventListener("click", useGeolocation);
$("btnRefresh").addEventListener("click", () => { fetchAll(); toast("RESYNCING ALL FEEDS…"); });
$("btnComp").addEventListener("click", () => { const b = $("compBox"); b.hidden = !b.hidden; });
$("btnSaveProfile").addEventListener("click", saveProfile);
$("btnSaveCheckin").addEventListener("click", saveCheckin);
$("btnExport").addEventListener("click", exportJSON);
$("btnClear").addEventListener("click", clearAll);
$("btnDismissEmergency").addEventListener("click", () => { $("emergencyOverlay").classList.remove("show"); renderAll(); });
window.addEventListener("resize", () => renderTimeline());

if (("serviceWorker" in navigator) && /^https?:$/.test(location.protocol)) {
  navigator.serviceWorker.register("service-worker.js").catch(() => {});
}

bootSequence();
startClock();
buildForms();
updateWhere();
renderHistory();
renderEvents();
fetchAll();
A.timers.push(setInterval(fetchAll, 5 * 60e3));
