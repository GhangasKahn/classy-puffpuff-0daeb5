import {
  cardinal, classifyWx, eyeLabel, faceCopy, fetchJson, fetchText, findPasses,
  fmtClock, fmtTime, groundTrack, lookAngles, parseTle, sgp4Look, sunAltitude,
  tileXY
} from "./astro.js";

const $ = (id) => document.getElementById(id);

function sizeCanvas(canvas) {
  const parent = canvas.parentElement;
  const w = Math.max(1, parent.clientWidth);
  const h = Math.max(1, parent.clientHeight);
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  canvas.style.width = w + "px";
  canvas.style.height = h + "px";
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w, h };
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
    status.textContent = `${how} · ${obs.lat.toFixed(4)}° ${obs.lon.toFixed(4)}°`;
    localStorage.setItem("op-loc", JSON.stringify(obs));
    if (notify) state.onLocation?.();
  };
  const saved = localStorage.getItem("op-loc");
  if (saved) {
    try { setObs(JSON.parse(saved), "Saved", false); } catch { /* keep Buffalo */ }
  }
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const lat = Number($("lat").value);
    const lon = Number($("lon").value);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) {
      status.textContent = "Coordinates out of range. Latitude ±90, longitude ±180.";
      return;
    }
    setObs({ lat, lon, altKm: 0.18 }, "Manual");
  });
  $("btn-buf").addEventListener("click", () => {
    setObs({ lat: 42.8864, lon: -78.8784, altKm: 0.18 }, "Buffalo preset");
  });
  $("btn-gps").addEventListener("click", () => {
    if (!navigator.geolocation) {
      status.textContent = "Geolocation is not in this browser. Enter coordinates or use Buffalo.";
      return;
    }
    status.textContent = "Requesting GPS…";
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setObs({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          altKm: (pos.coords.altitude || 180) / 1000
        }, "GPS");
      },
      (err) => {
        const fileish = location.protocol === "file:" || location.protocol === "content:";
        status.textContent = fileish
          ? "Local files block GPS. Serve over HTTPS or enter coordinates. Buffalo remains set."
          : `GPS failed (${err.message}). Buffalo remains set.`;
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
  const cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.42;

  ctx.strokeStyle = "#2e3026";
  ctx.lineWidth = 1;
  for (const el of [0, 30, 60]) {
    ctx.beginPath();
    ctx.arc(cx, cy, R * (1 - el / 90), 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.moveTo(cx, cy - R);
  ctx.lineTo(cx, cy + R);
  ctx.moveTo(cx - R, cy);
  ctx.lineTo(cx + R, cy);
  ctx.stroke();

  ctx.fillStyle = "#6e6a5e";
  ctx.font = "11px IBM Plex Mono, monospace";
  ctx.textAlign = "center";
  ctx.fillText("N", cx, cy - R - 8);
  ctx.fillText("S", cx, cy + R + 16);
  ctx.fillText("E", cx + R + 12, cy + 4);
  ctx.fillText("W", cx - R - 12, cy + 4);

  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const sweep = reduced ? 0 : (state.sweep || 0);
  ctx.strokeStyle = "#2e3026";
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + R * Math.sin(sweep * Math.PI / 180), cy - R * Math.cos(sweep * Math.PI / 180));
  ctx.stroke();

  const look = state.look;
  if (look && look.el > -5) {
    const r = R * Math.max(0, (90 - look.el) / 90);
    const a = look.az * Math.PI / 180;
    const x = cx + r * Math.sin(a);
    const y = cy - r * Math.cos(a);
    ctx.fillStyle = "#ff6a00";
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
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
  const cx = w / 2, cy = h / 2, R = 68;
  ctx.strokeStyle = "#2e3026";
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.stroke();
  ctx.fillStyle = "#6e6a5e";
  ctx.font = "11px IBM Plex Mono, monospace";
  ctx.textAlign = "center";
  ctx.fillText("N", cx, cy - R + 14);

  const target = state.look?.az ?? 0;
  state.easeCompass?.(target);
  const a = (state.compassNeedle || target) * Math.PI / 180;
  ctx.strokeStyle = "#d4c48a";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + (R - 8) * Math.sin(a), cy - (R - 8) * Math.cos(a));
  ctx.stroke();

  if (state.heading != null) {
    const hdg = state.heading * Math.PI / 180;
    ctx.strokeStyle = "#9a9486";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + (R - 18) * Math.sin(hdg), cy - (R - 18) * Math.cos(hdg));
    ctx.stroke();
  }
  $("compass-read").textContent = state.heading != null
    ? `Heading ${state.heading.toFixed(0)}° · FACE ${cardinal(target)}`
    : `FACE ${cardinal(target)} · device heading unavailable`;
}

export function drawTrack(state) {
  const canvas = $("ground-track");
  if (!canvas) return;
  const wrap = canvas.closest(".d4");
  if (wrap && getComputedStyle(wrap).display === "none") return;
  const { ctx, w, h } = sizeCanvas(canvas);
  ctx.fillStyle = "#1c1e16";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "#2e3026";
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
  const proj = (lat, lon) => [(lon + 180) / 360 * w, (90 - lat) / 180 * h];
  const pts = state.track || [];
  if (pts.length > 1) {
    ctx.strokeStyle = "#d4c48a";
    ctx.beginPath();
    pts.forEach((p, i) => {
      const [x, y] = proj(p.lat, p.lon);
      if (i && Math.abs(p.lon - pts[i - 1].lon) > 180) ctx.moveTo(x, y);
      else if (i) ctx.lineTo(x, y);
      else ctx.moveTo(x, y);
    });
    ctx.stroke();
  }
  if (state.iss) {
    const [x, y] = proj(state.iss.latitude, state.iss.longitude);
    ctx.fillStyle = "#ff6a00";
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
  }
  if (state.obs) {
    const [x, y] = proj(state.obs.lat, state.obs.lon);
    ctx.strokeStyle = "#e6e1d4";
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.stroke();
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
  $("iss-alt").textContent = iss.altitude.toFixed(1) + " km";
  $("iss-vel").textContent = iss.velocity.toFixed(0) + " km/h";
  $("iss-vis").textContent = iss.visibility;
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
  $("az").textContent = look.az.toFixed(1) + "°";
  $("el").textContent = look.el.toFixed(1) + "°";
  $("range").textContent = look.range.toFixed(0) + " km";
  $("mag").textContent = mag == null ? "—" : mag.toFixed(1) + " EST";
  $("face").textContent = faceCopy({ az: look.az, el: look.el, range: look.range, label });
}

export function paintWeather(state) {
  const wx = state.wx;
  if (!wx) {
    $("gate-word").textContent = "UNREAD";
    $("gate-why").textContent = state.wxError || "Weather not yet read.";
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
      const hh = t.slice(11, 16);
      li.innerHTML = `<span>${hh}</span><b>${g.cls.slice(0, 4).toUpperCase()}</b>`;
      list.appendChild(li);
    });
  } else {
    $("hourly-empty").hidden = false;
  }
}

export function paintPasses(state) {
  const body = $("pass-body");
  const nextWhen = $("next-when");
  const nextMeta = $("next-meta");
  const note = $("manifest-note");
  if (state.tleError) {
    body.innerHTML = `<tr><td colspan="6">TLE failed: ${state.tleError}</td></tr>`;
    nextWhen.textContent = "—";
    nextMeta.textContent = "Celestrak GP blocked or empty. ISS live lock still uses Where The ISS At.";
    note.textContent = state.tleError;
    return;
  }
  const passes = state.passes || [];
  if (!passes.length) {
    body.innerHTML = `<tr><td colspan="6">No 10° passes in the next 36 hours from this location.</td></tr>`;
    nextWhen.textContent = "None in 36 h";
    nextMeta.textContent = "SGP4 run complete.";
    note.textContent = "No 10° passes in the next 36 hours.";
    return;
  }
  const upcoming = passes.filter((p) => p.los > Date.now());
  const n = upcoming[0] || passes[0];
  const now = Date.now();
  const inView = n.aos <= now && n.los > now;
  const imminent = !inView && n.aos - now < 10 * 60 * 1000 && n.aos > now;
  $("next-pass").classList.toggle("is-imminent", imminent || inView);
  nextWhen.textContent = inView ? "IN VIEW" : imminent ? "IMMINENT" : fmtTime(n.aos);
  nextMeta.textContent = `${n.eye} · max el ${n.maxEl.toFixed(0)}°`;
  body.innerHTML = "";
  upcoming.slice(0, 12).forEach((p) => {
    const wx = wxAt(state.wx?.hourly, p.maxT);
    const tr = document.createElement("tr");
    const eyeClass = p.eye === "NAKED-EYE" ? "eye-naked" : p.eye === "DAY" ? "eye-day" : "eye-ecl";
    tr.innerHTML = `
      <td>${p.aos <= Date.now() && p.los > Date.now() ? "in view" : fmtTime(p.aos)}</td>
      <td>${fmtTime(p.maxT)}</td>
      <td>${fmtTime(p.los)}</td>
      <td>${p.maxEl.toFixed(0)}°</td>
      <td class="${eyeClass}">${p.eye}</td>
      <td>${wx.cls.toUpperCase()}</td>`;
    body.appendChild(tr);
  });
  note.textContent = `${upcoming.length} passes from Celestrak GP + SGP4. Weather class from Open-Meteo hourly at max-el hour.`;
}

export function paintRadar(state) {
  const img = $("radar-img");
  const empty = $("radar-empty");
  if (state.radarError || !state.radarUrl) {
    img.hidden = true;
    empty.hidden = false;
    empty.textContent = state.radarError || "RainViewer returned no frames.";
    return;
  }
  empty.hidden = true;
  img.hidden = false;
  img.src = state.radarUrl;
}

export function paintKp(state) {
  if (state.kp == null) {
    $("kp").textContent = "—";
    $("kp-src").textContent = state.kpError || "SWPC unread.";
    return;
  }
  $("kp").textContent = String(state.kp);
  $("kp-src").textContent = "NOAA SWPC planetary K-index (1-minute)";
}

export function paintStarship(state) {
  const el = $("starship-status");
  const ro = $("starship-readout");
  if (state.starshipError) {
    el.textContent = `Catalog query failed: ${state.starshipError}`;
    return;
  }
  if (!state.starship) {
    el.textContent = "No Starship elements in the current Celestrak GP catalog. Slot empty. No substitute constellation.";
    ro.hidden = true;
    return;
  }
  el.textContent = `Catalog hit: ${state.starship.OBJECT_NAME} · NORAD ${state.starship.NORAD_CAT_ID}.`;
  ro.hidden = false;
  ro.innerHTML = `
    <div><dt>Epoch</dt><dd>${state.starship.EPOCH}</dd></div>
    <div><dt>Inclination</dt><dd>${state.starship.INCLINATION}°</dd></div>
    <div><dt>Mean motion</dt><dd>${state.starship.MEAN_MOTION}</dd></div>`;
}

export async function loadIss(state) {
  try {
    state.iss = await fetchJson("https://api.wheretheiss.at/v1/satellites/25544");
    state.issError = null;
    paintLock(state);
  } catch (e) {
    state.issError = e.message;
    $("face").textContent = `FACE — ISS feed failed (${e.message}).`;
  }
}

export async function loadTle(state) {
  try {
    const text = await fetchText("https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle");
    const tle = parseTle(text);
    if (!window.satellite) throw new Error("satellite.js not loaded");
    state.satrec = window.satellite.twoline2satrec(tle.l1, tle.l2);
    state.tleError = null;
    state.passes = findPasses(state.satrec, state.obs);
    state.track = groundTrack(state.satrec);
    paintPasses(state);
    state.drawTrack?.();
  } catch (e) {
    state.tleError = `Celestrak GP CORS or network: ${e.message}`;
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
  $("btn-ar").addEventListener("click", async () => {
    const proto = location.protocol;
    if (proto === "file:" || proto === "content:") {
      msg.textContent = "Camera is not available on content:// or file://. FACE remains the source of truth. Serve over HTTPS.";
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      msg.textContent = "This browser has no camera API. FACE remains the source of truth.";
      return;
    }
    if (typeof DeviceOrientationEvent !== "undefined" && typeof DeviceOrientationEvent.requestPermission === "function") {
      try { await DeviceOrientationEvent.requestPermission(); } catch { /* still try camera */ }
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false
      });
      video.srcObject = stream;
      await video.play();
      msg.textContent = "HUD live. FACE line is still authoritative if compass variance is large.";
      state.arOn = true;
    } catch (e) {
      msg.textContent = `Camera denied or failed (${e.message}). HUD-only: use FACE.`;
    }
  });

  const drawHud = () => {
    requestAnimationFrame(drawHud);
    if (!state.arOn || !hud) return;
    const parent = hud.parentElement;
    const w = parent.clientWidth, h = parent.clientHeight;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    hud.width = w * dpr;
    hud.height = h * dpr;
    hud.style.width = w + "px";
    hud.style.height = h + "px";
    const ctx = hud.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const look = state.look;
    if (!look) return;
    const heading = state.heading ?? look.az;
    const daz = ((look.az - heading + 540) % 360) - 180;
    const x = w / 2 + (daz / 30) * (w / 2);
    const y = h * 0.75 - (look.el / 90) * (h * 0.55);
    ctx.strokeStyle = "#ff6a00";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(Math.max(12, Math.min(w - 12, x)), Math.max(12, Math.min(h - 12, y)), 14, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = "#e6e1d4";
    ctx.beginPath();
    ctx.moveTo(w / 2, h * 0.75);
    ctx.lineTo(Math.max(12, Math.min(w - 12, x)), Math.max(12, Math.min(h - 12, y)));
    ctx.stroke();
    ctx.fillStyle = "#e6e1d4";
    ctx.font = "12px IBM Plex Mono, monospace";
    ctx.fillText(`EL ${look.el.toFixed(0)}°  ΔAZ ${daz.toFixed(0)}°`, 12, 20);
  };
  drawHud();
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
