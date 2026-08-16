import {
  cardinal, classifyWx, eyeLabel, faceCopy, fetchJson, fetchText, findPasses,
  fmtClock, fmtTime, groundTrack, lookAngles, parseTle, sgp4Look, sunAltitude,
  tileXY, waitForSatellite
} from "./astro.js";

const $ = (id) => document.getElementById(id);

function sizeCanvas(canvas) {
  const parent = canvas.parentElement;
  const w = Math.max(1, parent.clientWidth);
  const h = Math.max(1, parent.clientHeight);
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const bw = Math.round(w * dpr);
  const bh = Math.round(h * dpr);
  if (canvas.width !== bw || canvas.height !== bh) {
    canvas.width = bw;
    canvas.height = bh;
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w, h };
}

function setNum(el, text) {
  if (!el) return;
  if (el.textContent === text) return;
  el.textContent = text;
  el.classList.remove("is-settle");
  void el.offsetWidth;
  el.classList.add("is-settle");
}

export function bindDepth(state) {
  const stored = localStorage.getItem("op-depth");
  if (stored && "1234".includes(stored)) document.body.dataset.depth = stored;
  const apply = (n) => {
    document.body.dataset.depth = String(n);
    localStorage.setItem("op-depth", String(n));
    document.querySelectorAll(".depth-btn").forEach((b) => {
      b.setAttribute("aria-checked", b.dataset.depth === String(n) ? "true" : "false");
    });
    state.showDepthToast?.(n);
    requestAnimationFrame(() => {
      state.drawPlot?.();
      state.drawTrack?.();
    });
  };
  document.querySelectorAll(".depth-btn").forEach((b) => {
    b.addEventListener("click", () => apply(Number(b.dataset.depth)));
  });
  apply(Number(document.body.dataset.depth || 2));
}

export function bindLocation(state) {
  const form = $("loc-form");
  const status = $("loc-status");
  const setObs = (obs, how, notify = true) => {
    state.obs = obs;
    $("lat").value = obs.lat.toFixed(4);
    $("lon").value = obs.lon.toFixed(4);
    status.textContent = `${how} · ${obs.lat.toFixed(4)}°N ${Math.abs(obs.lon).toFixed(4)}°W`;
    localStorage.setItem("op-loc", JSON.stringify(obs));
    if (notify) state.onLocation?.();
  };
  const saved = localStorage.getItem("op-loc");
  if (saved) {
    try { setObs(JSON.parse(saved), "Saved Position", false); } catch { /* keep Buffalo */ }
  }
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const lat = Number($("lat").value);
    const lon = Number($("lon").value);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) {
      status.textContent = "Coordinates out of range. Latitude ±90, longitude ±180.";
      return;
    }
    setObs({ lat, lon, altKm: 0.18 }, "Manual Fix");
  });
  $("btn-buf").addEventListener("click", () => {
    setObs({ lat: 42.8864, lon: -78.8784, altKm: 0.18 }, "Buffalo preset");
  });
  $("btn-gps").addEventListener("click", () => {
    if (!navigator.geolocation) {
      status.textContent = "Geolocation unsupported in browser. Using manual coordinates.";
      return;
    }
    status.textContent = "Acquiring GPS fix…";
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setObs({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          altKm: (pos.coords.altitude || 180) / 1000
        }, "GPS Fix");
        state.audio?.playPassAlert();
      },
      (err) => {
        const fileish = location.protocol === "file:" || location.protocol === "content:";
        status.textContent = fileish
          ? "Local file protocol blocks GPS. Buffalo preset active."
          : `GPS fix failed (${err.message}). Buffalo active.`;
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  });
}

export function drawSkyPlot(state) {
  const canvas = $("sky-plot");
  const wrap = canvas?.closest(".plot-wrap");
  if (!canvas || (wrap && getComputedStyle(wrap).display === "none")) return;
  const { ctx, w, h } = sizeCanvas(canvas);
  ctx.clearRect(0, 0, w, h);
  const cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.43;

  // Background Grid Rings
  ctx.strokeStyle = "rgba(0, 229, 255, 0.15)";
  ctx.lineWidth = 1;
  for (const el of [30, 60]) {
    ctx.beginPath();
    ctx.arc(cx, cy, R * (1 - el / 90), 0, Math.PI * 2);
    ctx.stroke();
  }

  // Outer Horizon Ring (Vivid Cyan Glow)
  ctx.strokeStyle = "#00e5ff";
  ctx.lineWidth = 1.5;
  ctx.shadowColor = "rgba(0, 229, 255, 0.6)";
  ctx.shadowBlur = 8;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Crosshairs
  ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(cx, cy - R);
  ctx.lineTo(cx, cy + R);
  ctx.moveTo(cx - R, cy);
  ctx.lineTo(cx + R, cy);
  ctx.stroke();

  // Cardinal Labels
  ctx.fillStyle = "#00e5ff";
  ctx.font = "bold 11px Space Mono, monospace";
  ctx.textAlign = "center";
  ctx.fillText("N (000°)", cx, cy - R - 8);
  ctx.fillText("S (180°)", cx, cy + R + 18);
  ctx.fillText("E", cx + R + 14, cy + 4);
  ctx.fillText("W", cx - R - 14, cy + 4);
  
  ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
  ctx.font = "9px Space Mono, monospace";
  ctx.fillText("30°", cx + 6, cy - R * (1 - 30 / 90) + 3);
  ctx.fillText("60°", cx + 6, cy - R * (1 - 60 / 90) + 3);

  // Vivid Amber Sweep Radar Line
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const sweep = reduced ? 0 : (state.sweep || 0);
  const sweepRad = sweep * Math.PI / 180;
  
  // Sweep beam gradient
  const sweepGrad = ctx.createLinearGradient(cx, cy, cx + R * Math.sin(sweepRad), cy - R * Math.cos(sweepRad));
  sweepGrad.addColorStop(0, "rgba(255, 170, 0, 0.9)");
  sweepGrad.addColorStop(1, "rgba(255, 85, 0, 0.1)");
  
  ctx.strokeStyle = sweepGrad;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + R * Math.sin(sweepRad), cy - R * Math.cos(sweepRad));
  ctx.stroke();

  // Target Satellite Pip (Brutalist Diamond Reticle with Pulsing Core)
  const look = state.look;
  if (look && look.el > -5) {
    const r = R * Math.max(0, (90 - look.el) / 90);
    const a = look.az * Math.PI / 180;
    const x = cx + r * Math.sin(a);
    const y = cy - r * Math.cos(a);

    // Outer Target Reticle
    ctx.strokeStyle = "#ff5500";
    ctx.lineWidth = 1.5;
    ctx.shadowColor = "#ff5500";
    ctx.shadowBlur = 12;
    ctx.strokeRect(x - 6, y - 6, 12, 12);
    
    // Cross marks
    ctx.beginPath();
    ctx.moveTo(x - 10, y);
    ctx.lineTo(x + 10, y);
    ctx.moveTo(x, y - 10);
    ctx.lineTo(x, y + 10);
    ctx.stroke();

    // Hot Center Core
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  }
}

export function drawCompass(state) {
  const canvas = $("compass");
  if (!canvas) return;
  const wrap = canvas.closest(".d3");
  if (wrap && getComputedStyle(wrap).display === "none") return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const cx = w / 2, cy = h / 2, R = 64;

  // Outer Ring
  ctx.strokeStyle = "rgba(0, 229, 255, 0.3)";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.stroke();

  // Dial Ticks
  for (let deg = 0; deg < 360; deg += 15) {
    const a = deg * Math.PI / 180;
    const inner = deg % 90 === 0 ? R - 10 : deg % 45 === 0 ? R - 7 : R - 4;
    ctx.strokeStyle = deg % 90 === 0 ? "#00e5ff" : "rgba(255, 255, 255, 0.25)";
    ctx.beginPath();
    ctx.moveTo(cx + inner * Math.sin(a), cy - inner * Math.cos(a));
    ctx.lineTo(cx + R * Math.sin(a), cy - R * Math.cos(a));
    ctx.stroke();
  }

  ctx.fillStyle = "#00e5ff";
  ctx.font = "bold 11px Space Mono, monospace";
  ctx.textAlign = "center";
  ctx.fillText("N", cx, cy - R + 18);

  // Target Azimuth Vector Needle
  const target = state.look?.az ?? 0;
  state.easeCompass?.(target);
  const a = (state.compassNeedle || target) * Math.PI / 180;
  
  ctx.strokeStyle = "#ff5500";
  ctx.lineWidth = 2.5;
  ctx.shadowColor = "#ff5500";
  ctx.shadowBlur = 10;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + (R - 6) * Math.sin(a), cy - (R - 6) * Math.cos(a));
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Device Physical Orientation Bearing
  if (state.heading != null) {
    const hdg = state.heading * Math.PI / 180;
    ctx.strokeStyle = "#00e5ff";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + (R - 16) * Math.sin(hdg), cy - (R - 16) * Math.cos(hdg));
    ctx.stroke();
  }

  $("compass-read").textContent = state.heading != null
    ? `HEADING ${state.heading.toFixed(0)}° // TARGET ${cardinal(target)}`
    : `TARGET BEARING ${cardinal(target)} (${target.toFixed(0)}°)`;
}

export function drawTrack(state) {
  const canvas = $("ground-track");
  if (!canvas) return;
  const wrap = canvas.closest(".d4");
  if (wrap && getComputedStyle(wrap).display === "none") return;
  const { ctx, w, h } = sizeCanvas(canvas);
  
  ctx.fillStyle = "#07090e";
  ctx.fillRect(0, 0, w, h);
  
  // Latitude / Longitude Grid
  ctx.strokeStyle = "rgba(34, 45, 61, 0.8)";
  ctx.lineWidth = 1;
  for (let i = 1; i < 4; i++) {
    ctx.beginPath();
    ctx.moveTo(0, h * i / 4);
    ctx.lineTo(w, h * i / 4);
    ctx.stroke();
  }
  for (let i = 1; i < 6; i++) {
    ctx.beginPath();
    ctx.moveTo(w * i / 6, 0);
    ctx.lineTo(w * i / 6, h);
    ctx.stroke();
  }

  ctx.fillStyle = "#4e5e73";
  ctx.font = "9px Space Mono, monospace";
  ctx.textAlign = "left";
  ctx.fillText("+90°", 4, 12);
  ctx.fillText("-90°", 4, h - 6);
  ctx.textAlign = "center";
  ctx.fillText("0° (EQUATOR)", w / 2, h / 2 - 4);

  const proj = (lat, lon) => [(lon + 180) / 360 * w, (90 - lat) / 180 * h];
  const pts = state.track || [];
  
  // SGP4 Ground Track Sine Trajectory
  if (pts.length > 1) {
    ctx.strokeStyle = "#00e5ff";
    ctx.lineWidth = 2;
    ctx.shadowColor = "#00e5ff";
    ctx.shadowBlur = 8;
    ctx.beginPath();
    pts.forEach((p, i) => {
      const [x, y] = proj(p.lat, p.lon);
      if (i && Math.abs(p.lon - pts[i - 1].lon) > 180) ctx.moveTo(x, y);
      else if (i) ctx.lineTo(x, y);
      else ctx.moveTo(x, y);
    });
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  // ISS Sub-Satellite Point
  if (state.iss) {
    const [x, y] = proj(state.iss.latitude, state.iss.longitude);
    ctx.fillStyle = "#ff5500";
    ctx.shadowColor = "#ff5500";
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  // Observer Location Marker
  if (state.obs) {
    const [x, y] = proj(state.obs.lat, state.obs.lon);
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.5;
    ctx.strokeRect(x - 4, y - 4, 8, 8);
  }
}

function wxAt(hourly, ms) {
  if (!hourly?.time) return { cls: "unknown", why: "—" };
  const iso = new Date(ms).toISOString().slice(0, 13);
  let idx = hourly.time.findIndex((t) => t.startsWith(iso));
  if (idx < 0) idx = hourly.time.findIndex((t) => new Date(t).getTime() >= ms);
  if (idx < 0) return { cls: "unknown", why: "—" };
  return classifyWx(hourly.cloud_cover[idx], hourly.precipitation[idx], hourly.visibility?.[idx]);
}

export function paintLock(state) {
  $("clock").textContent = fmtClock(Date.now());
  const iss = state.iss;
  if (!iss) return;
  $("iss-lat").textContent = iss.latitude.toFixed(4) + "°";
  $("iss-lon").textContent = iss.longitude.toFixed(4) + "°";
  $("iss-alt").textContent = iss.altitude.toFixed(1) + " KM";
  $("iss-vel").textContent = iss.velocity.toFixed(0) + " KM/H";
  $("iss-vis").textContent = (iss.visibility || "").toUpperCase();
  $("iss-ts").textContent = new Date(iss.timestamp * 1000).toISOString();

  const look = lookAngles(state.obs, { lat: iss.latitude, lon: iss.longitude, altKm: iss.altitude });
  const sunAlt = sunAltitude(state.obs.lat, state.obs.lon, new Date());
  let eclipsed = iss.visibility === "eclipsed";
  let mag = null;
  if (state.satrec) {
    const s = sgp4Look(state.satrec, state.obs, new Date());
    if (s) {
      eclipsed = s.eclipsed;
      mag = s.mag;
    }
  }
  const label = eyeLabel({ el: look.el, eclipsed, sunAlt });
  state.look = { ...look, mag, label, eclipsed };
  
  setNum($("az"), look.az.toFixed(1) + "°");
  setNum($("el"), look.el.toFixed(1) + "°");
  setNum($("range"), look.range.toFixed(0) + " KM");
  setNum($("mag"), mag == null ? "—" : mag.toFixed(1) + " EST");
  $("face").textContent = faceCopy({ az: look.az, el: look.el, range: look.range, label });
}

export function paintWeather(state) {
  const wx = state.wx;
  if (!wx) {
    $("gate-word").textContent = "SCANNING";
    $("gate-why").textContent = state.wxError || "Awaiting atmospheric data.";
    $("gate").dataset.class = "unknown";
    return;
  }
  const c = wx.current;
  const gate = classifyWx(c.cloud_cover, c.precipitation, c.visibility);
  $("gate").dataset.class = gate.cls;
  $("gate-word").textContent = gate.cls.toUpperCase();
  $("gate-why").textContent = gate.why;
  
  const hours = wx.hourly;
  const list = $("hourly-list");
  list.innerHTML = "";
  if (hours?.time) {
    $("hourly-empty").hidden = true;
    hours.time.slice(0, 12).forEach((t, i) => {
      const g = classifyWx(hours.cloud_cover[i], hours.precipitation[i], hours.visibility?.[i]);
      const li = document.createElement("li");
      li.dataset.class = g.cls;
      const t0 = Date.parse(t);
      if (Number.isFinite(t0) && (state.passes || []).some((p) => p.maxT >= t0 && p.maxT < t0 + 36e5)) {
        li.dataset.pass = "1";
      }
      const hh = t.slice(11, 16);
      li.innerHTML = `<span>${hh}</span><b>${g.cls.slice(0, 4).toUpperCase()}</b>`;
      list.appendChild(li);
    });
  } else {
    $("hourly-empty").hidden = false;
  }
}

function fillPassTable(tbody, upcoming, hourly) {
  if (!tbody) return;
  tbody.innerHTML = "";
  upcoming.forEach((p) => {
    const wx = wxAt(hourly, p.maxT);
    const tr = document.createElement("tr");
    const eyeClass = p.eye === "NAKED-EYE" ? "eye-naked" : p.eye === "DAY" ? "eye-day" : "eye-ecl";
    tr.innerHTML = `
      <td>${p.aos <= Date.now() && p.los > Date.now() ? "IN VIEW NOW" : fmtTime(p.aos)}</td>
      <td>${fmtTime(p.maxT)}</td>
      <td>${fmtTime(p.los)}</td>
      <td>${p.maxEl.toFixed(0)}°</td>
      <td class="${eyeClass}">${p.eye}</td>
      <td>${wx.cls.toUpperCase()}</td>`;
    tbody.appendChild(tr);
  });
}

export function paintPasses(state) {
  const body = $("pass-body");
  const manifest = $("manifest-body");
  const nextWhen = $("next-when");
  const nextMeta = $("next-meta");
  const note = $("manifest-note");
  
  if (state.tleError) {
    const msg = `<tr><td colspan="6">TLE Sync Error: ${state.tleError}</td></tr>`;
    body.innerHTML = msg;
    if (manifest) manifest.innerHTML = msg;
    nextWhen.textContent = "OFFLINE";
    nextMeta.textContent = "Direct ISS position still live via WhereTheISS.";
    note.textContent = state.tleError;
    return;
  }
  
  const passes = state.passes || [];
  if (!passes.length) {
    const msg = `<tr><td colspan="6">Zero 10° elevation passes in the next 36 hours for this position.</td></tr>`;
    body.innerHTML = msg;
    if (manifest) manifest.innerHTML = msg;
    nextWhen.textContent = "NONE (36H)";
    nextMeta.textContent = "SGP4 search complete.";
    note.textContent = "No passes &gt;10° elevation in 36h.";
    return;
  }
  
  const upcoming = passes.filter((p) => p.los > Date.now());
  const n = upcoming[0] || passes[0];
  const now = Date.now();
  const inView = n.aos <= now && n.los > now;
  const imminent = !inView && n.aos - now < 10 * 60 * 1000 && n.aos > now;
  
  $("next-pass").classList.toggle("is-imminent", imminent || inView);
  nextWhen.textContent = inView ? "IN VIEW NOW" : imminent ? "IMMINENT" : fmtTime(n.aos);
  nextMeta.textContent = `${n.eye} · PEAK EL ${n.maxEl.toFixed(0)}°`;
  
  fillPassTable(body, upcoming.slice(0, 12), state.wx?.hourly);
  fillPassTable(manifest, upcoming.slice(0, 12), state.wx?.hourly);
  note.textContent = `${upcoming.length} passes computed via Celestrak NORAD GP + SGP4.`;
}

export function paintRadar(state) {
  const img = $("radar-img");
  const empty = $("radar-empty");
  const cap = $("radar-cap");
  const well = $("radar-well");
  
  if (state.radarError || !state.radarUrl) {
    img.hidden = true;
    empty.hidden = false;
    empty.textContent = state.radarError || "RainViewer radar tiles unavailable.";
    well.classList.remove("has-tile");
    if (cap) cap.textContent = "Radar Offline";
    return;
  }
  
  empty.hidden = true;
  img.hidden = false;
  img.src = state.radarUrl;
  well.classList.add("has-tile");
  if (cap) {
    const when = state.radarTime ? new Date(state.radarTime * 1000).toISOString().slice(11, 16) + " UTC" : "—";
    cap.textContent = `RainViewer Doppler Array · ${when} · Observer Center Reticle`;
  }
}

export function paintKp(state) {
  if (state.kp == null) {
    $("kp").textContent = "—";
    $("kp-src").textContent = state.kpError || "SWPC offline.";
    return;
  }
  $("kp").textContent = String(state.kp);
  $("kp-src").textContent = "NOAA SWPC planetary K-index (1-minute)";
}

export function paintStarship(state) {
  const el = $("starship-status");
  const ro = $("starship-readout");
  if (state.starshipError) {
    el.textContent = `Catalog query: ${state.starshipError}`;
    return;
  }
  if (!state.starship) {
    el.textContent = "No Starship elements currently in Celestrak GP repository. Slot empty. Zero artificial constellation bloat.";
    ro.hidden = true;
    return;
  }
  el.textContent = `Catalog hit: ${state.starship.OBJECT_NAME} · NORAD ${state.starship.NORAD_CAT_ID}.`;
  ro.hidden = false;
  let lookHtml = "";
  try {
    const sat = window.satellite;
    if (sat?.json2satrec && state.obs) {
      const rec = sat.json2satrec(state.starship);
      const look = sgp4Look(rec, state.obs, new Date());
      if (look) {
        lookHtml = `
    <div><dt>Look AZ</dt><dd>${look.az.toFixed(1)}°</dd></div>
    <div><dt>Look EL</dt><dd>${look.el.toFixed(1)}°</dd></div>`;
      }
    }
  } catch {}
  ro.innerHTML = `
    <div><dt>Epoch</dt><dd>${state.starship.EPOCH}</dd></div>
    <div><dt>Inclination</dt><dd>${state.starship.INCLINATION}°</dd></div>
    <div><dt>Mean Motion</dt><dd>${state.starship.MEAN_MOTION}</dd></div>${lookHtml}`;
}

export async function loadIss(state) {
  try {
    state.iss = await fetchJson("https://api.wheretheiss.at/v1/satellites/25544");
    state.issError = null;
    paintLock(state);
    state.audio?.playLockTick();
  } catch (e) {
    state.issError = e.message;
    $("face").textContent = `FACE — ISS telemetry link offline (${e.message}).`;
  }
}

export async function loadTle(state) {
  try {
    await waitForSatellite();
    let text;
    try {
      text = await fetchText("https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle", 6000);
    } catch {
      // Direct secondary fallback to celestrak mirror
      text = await fetchText("https://celestrak.com/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle", 6000);
    }
    const tle = parseTle(text);
    state.satrec = window.satellite.twoline2satrec(tle.l1, tle.l2);
    state.tleError = null;
    state.passes = findPasses(state.satrec, state.obs);
    state.track = groundTrack(state.satrec, state.obs);
    paintPasses(state);
    if (state.wx) paintWeather(state);
    state.drawTrack?.();
  } catch (e) {
    state.tleError = `Celestrak GP link: ${e.message}`;
    paintPasses(state);
  }
}

export async function loadWeather(state) {
  try {
    const { lat, lon } = state.obs;
    state.wx = await fetchJson(
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=cloud_cover,precipitation,visibility&hourly=cloud_cover,precipitation,visibility&forecast_days=2&timezone=auto`
    );
    state.wxError = null;
    paintWeather(state);
    paintPasses(state);
  } catch (e) {
    state.wxError = e.message;
    paintWeather(state);
  }
}

export async function loadRadar(state) {
  try {
    const maps = await fetchJson("https://api.rainviewer.com/public/weather-maps.json");
    const frames = maps?.radar?.past || [];
    if (!frames.length) {
      state.radarUrl = null;
      state.radarError = "RainViewer past frames empty.";
      paintRadar(state);
      return;
    }
    const last = frames[frames.length - 1];
    const { x, y, z } = tileXY(state.obs.lat, state.obs.lon, 6);
    state.radarUrl = `${maps.host}${last.path}/256/${z}/${x}/${y}/2/1_1.png`;
    state.radarTime = last.time;
    state.radarError = null;
    paintRadar(state);
  } catch (e) {
    state.radarError = e.message;
    state.radarUrl = null;
    paintRadar(state);
  }
}

export async function loadKp(state) {
  try {
    const rows = await fetchJson("https://services.swpc.noaa.gov/json/planetary_k_index_1m.json");
    const last = rows[rows.length - 1];
    state.kp = last?.kp_index ?? last?.estimated_kp ?? null;
    state.kpError = null;
    paintKp(state);
  } catch (e) {
    state.kpError = e.message;
    paintKp(state);
  }
}

export async function loadStarship(state) {
  try {
    const res = await fetch("https://celestrak.org/NORAD/elements/gp.php?NAME=STARSHIP&FORMAT=json");
    if (res.status === 404) {
      state.starship = null;
      state.starshipError = null;
      paintStarship(state);
      return;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const rows = await res.json();
    state.starship = Array.isArray(rows) && rows.length ? rows[0] : null;
    state.starshipError = null;
    paintStarship(state);
  } catch (e) {
    state.starshipError = e.message;
    paintStarship(state);
  }
}

export function bindHeading(state) {
  const apply = (e) => {
    let hdg = null;
    if (typeof e.webkitCompassHeading === "number") hdg = e.webkitCompassHeading;
    else if (e.absolute && typeof e.alpha === "number") hdg = (360 - e.alpha) % 360;
    if (hdg != null) {
      state.heading = hdg;
      drawCompass(state);
    }
  };
  window.addEventListener("deviceorientationabsolute", apply);
  window.addEventListener("deviceorientation", apply);
}

export function bindAr(state) {
  const msg = $("ar-msg");
  const video = $("ar-video");
  const hud = $("ar-hud");
  let raf = 0;
  
  $("btn-ar").addEventListener("click", async () => {
    state.audio?.playModeClick();
    const proto = location.protocol;
    if (proto === "file:" || proto === "content:") {
      msg.textContent = "Camera stream requires HTTPS. FACE bearing remains authoritative.";
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      msg.textContent = "Camera API unavailable in this environment. FACE line authoritative.";
      return;
    }
    if (typeof DeviceOrientationEvent !== "undefined" && typeof DeviceOrientationEvent.requestPermission === "function") {
      try { await DeviceOrientationEvent.requestPermission(); } catch {}
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false
      });
      video.srcObject = stream;
      await video.play();
      msg.textContent = "OPTICAL HUD ENGAGED // HARDWARE SENSOR SYNC ACTIVE";
      state.arOn = true;
      state.audio?.playPassAlert();
      if (!raf) raf = requestAnimationFrame(drawHud);
    } catch (e) {
      msg.textContent = `Camera permission denied (${e.message}). Reverting to HUD readout.`;
    }
  });

  const project = (look, heading, w, h) => {
    const daz = ((look.az - heading + 540) % 360) - 180;
    return {
      x: Math.max(14, Math.min(w - 14, w / 2 + (daz / 30) * (w / 2))),
      y: Math.max(14, Math.min(h - 14, h * 0.75 - (look.el / 90) * (h * 0.55)))
    };
  };

  const drawHud = () => {
    if (!state.arOn || !hud) {
      raf = 0;
      return;
    }
    raf = requestAnimationFrame(drawHud);
    const parent = hud.parentElement;
    const w = parent.clientWidth, h = parent.clientHeight;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    if (hud.width !== w * dpr || hud.height !== h * dpr) {
      hud.width = w * dpr;
      hud.height = h * dpr;
      hud.style.width = w + "px";
      hud.style.height = h + "px";
    }
    const ctx = hud.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    
    const look = state.look;
    if (!look) return;
    const heading = state.heading ?? look.az;
    
    // Trajectory Polyline
    if (state.satrec && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
      ctx.strokeStyle = "#00e5ff";
      ctx.lineWidth = 2;
      ctx.shadowColor = "#00e5ff";
      ctx.shadowBlur = 8;
      ctx.beginPath();
      for (let i = 0; i <= 8; i++) {
        const s = sgp4Look(state.satrec, state.obs, new Date(Date.now() + i * 30 * 1000));
        if (!s) continue;
        const p = project(s, heading, w, h);
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
      ctx.shadowBlur = 0;
    }
    
    // Target Reticle
    const p = project(look, heading, w, h);
    ctx.strokeStyle = "#ff5500";
    ctx.lineWidth = 2;
    ctx.shadowColor = "#ff5500";
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 16, 0, Math.PI * 2);
    ctx.stroke();
    
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 12px Space Mono, monospace";
    ctx.fillText(`EL ${look.el.toFixed(0)}°  ΔAZ ${(((look.az - heading + 540) % 360) - 180).toFixed(0)}°`, 12, 22);
  };
}

export function bindResize(state) {
  const ro = new ResizeObserver(() => {
    state.drawPlot?.();
    state.drawTrack?.();
    drawCompass(state);
  });
  ["sky-plot", "ground-track"].forEach((id) => {
    const el = $(id)?.parentElement;
    if (el) ro.observe(el);
  });
}
