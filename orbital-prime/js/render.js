import {
  cardinal, classifyWx, eyeLabel, faceCopy, findPassesAsync,
  fmtClock, fmtTime, groundTrack, lookAngles, parseAllTles, parseShareQuery, sgp4Look, sunAltitude,
  tileXY, waitForSatellite
} from "./astro.js?v=6";
import { getIss, getKp, getRadarIndex, getStations, getStarship, getTle, getWeather } from "./feeds.js?v=6";
import { issResidual, scorePass, wxSlice } from "./score.js?v=6";

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

export function fmtHemisphere(obs) {
  const ns = obs.lat >= 0 ? "N" : "S";
  const ew = obs.lon >= 0 ? "E" : "W";
  return `${Math.abs(obs.lat).toFixed(4)}°${ns} ${Math.abs(obs.lon).toFixed(4)}°${ew}`;
}

export function writeShare(state) {
  if (!state?.obs || typeof history === "undefined") return;
  const u = new URL(location.href);
  u.searchParams.set("lat", state.obs.lat.toFixed(4));
  u.searchParams.set("lon", state.obs.lon.toFixed(4));
  u.searchParams.set("sat", state.targetId || "25544");
  history.replaceState(null, "", u);
}

export function bindLocation(state) {
  const form = $("loc-form");
  const status = $("loc-status");
  const setObs = (obs, how, notify = true) => {
    state.obs = obs;
    $("lat").value = obs.lat.toFixed(4);
    $("lon").value = obs.lon.toFixed(4);
    status.textContent = `${how} · ${fmtHemisphere(obs)}`;
    localStorage.setItem("op-loc", JSON.stringify(obs));
    writeShare(state);
    if (notify) state.onLocation?.();
  };
  const share = parseShareQuery(location.search);
  if (share?.sat) {
    state.targetId = share.sat;
    localStorage.setItem("op-sat", share.sat);
  }
  if (share) {
    setObs({ lat: share.lat, lon: share.lon, altKm: 0.18 }, "Shared link", false);
  } else {
    const saved = localStorage.getItem("op-loc");
    if (saved) {
      try { setObs(JSON.parse(saved), "Saved position", false); } catch { /* keep Buffalo */ }
    }
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
  const cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.42;

  ctx.strokeStyle = "rgba(17, 17, 17, 0.22)";
  ctx.lineWidth = 1;
  for (const el of [30, 60]) {
    ctx.beginPath();
    ctx.arc(cx, cy, R * (1 - el / 90), 0, Math.PI * 2);
    ctx.stroke();
  }

  ctx.strokeStyle = "#111111";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.stroke();

  (state.passes || []).filter((p) => p.los > Date.now()).slice(0, 5).forEach((p) => {
    const az0 = p.samples?.[0]?.az;
    if (az0 == null) return;
    const a = az0 * Math.PI / 180;
    const x = cx + R * Math.sin(a);
    const y = cy - R * Math.cos(a);
    ctx.fillStyle = p.eye === "NAKED-EYE" ? "#ffe600" : "#111111";
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  });

  ctx.strokeStyle = "rgba(17, 17, 17, 0.28)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(cx, cy - R);
  ctx.lineTo(cx, cy + R);
  ctx.moveTo(cx - R, cy);
  ctx.lineTo(cx + R, cy);
  ctx.stroke();

  ctx.fillStyle = "#111111";
  ctx.font = "700 11px 'Space Mono', monospace";
  ctx.textAlign = "center";
  ctx.fillText("N", cx, cy - R - 8);
  ctx.fillText("S", cx, cy + R + 16);
  ctx.fillText("E", cx + R + 12, cy + 4);
  ctx.fillText("W", cx - R - 12, cy + 4);

  ctx.fillStyle = "#6b6458";
  ctx.font = "9px 'Space Mono', monospace";
  ctx.fillText("30", cx + 8, cy - R * (1 - 30 / 90) + 3);
  ctx.fillText("60", cx + 8, cy - R * (1 - 60 / 90) + 3);

  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const sweep = reduced ? 0 : (state.sweep || 0);
  const sweepRad = sweep * Math.PI / 180;
  ctx.strokeStyle = "#ff5a00";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + R * Math.sin(sweepRad), cy - R * Math.cos(sweepRad));
  ctx.stroke();

  const look = state.look;
  if (look && look.el > -5) {
    const r = R * Math.max(0, (90 - look.el) / 90);
    const a = look.az * Math.PI / 180;
    const x = cx + r * Math.sin(a);
    const y = cy - r * Math.cos(a);
    ctx.strokeStyle = "#111111";
    ctx.lineWidth = 2;
    ctx.strokeRect(x - 5, y - 5, 10, 10);
    ctx.fillStyle = "#ff5a00";
    ctx.fillRect(x - 2, y - 2, 4, 4);
  }
}

/* AMG-cluster segmented gauge: discrete ember tick segments with layered
   bloom (no shadowBlur in the loop — two-pass strokes keep 60fps on mobile),
   thin digital core numeral. The lit edge IS the needle, like the real cluster. */
function hexRgb(hex) {
  return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
}

function drawArcGauge(canvas, cfg) {
  const parent = canvas.parentElement;
  const w = Math.max(1, parent.clientWidth);
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const bw = Math.round(w * dpr);
  if (canvas.width !== bw || canvas.height !== bw) {
    canvas.width = bw;
    canvas.height = bw;
    canvas.style.width = w + "px";
    canvas.style.height = w + "px";
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, w);

  const cx = w / 2, cy = w / 2;
  const R = w * 0.42;
  const START = Math.PI * 0.75;           // 135° — bottom left
  const SWEEP = Math.PI * 1.5;            // 270° clockwise
  const frac = Math.max(0, Math.min(1, (cfg.value - cfg.min) / (cfg.max - cfg.min)));

  const SEGS = 36;
  const litCount = Math.round(frac * SEGS);
  const c0 = hexRgb(cfg.color0 || "#111111");
  const c1 = hexRgb(cfg.color1 || "#ff5a00");

  ctx.lineCap = "butt";
  for (let i = 0; i < SEGS; i++) {
    const f = i / (SEGS - 1);
    const lit = i < litCount;
    const a = START + SWEEP * f;
    const major = i % 4 === 0;
    const rIn = R - w * (major ? 0.12 : 0.08);
    const r = Math.round(c0[0] + (c1[0] - c0[0]) * f);
    const g = Math.round(c0[1] + (c1[1] - c0[1]) * f);
    const b = Math.round(c0[2] + (c1[2] - c0[2]) * f);
    ctx.strokeStyle = lit ? `rgb(${r}, ${g}, ${b})` : "rgba(17, 17, 17, 0.18)";
    ctx.lineWidth = Math.max(2, w * 0.018);
    ctx.beginPath();
    ctx.moveTo(cx + rIn * Math.cos(a), cy + rIn * Math.sin(a));
    ctx.lineTo(cx + R * Math.cos(a), cy + R * Math.sin(a));
    ctx.stroke();
  }

  if (litCount > 0) {
    const a = START + SWEEP * ((litCount - 1) / (SEGS - 1));
    ctx.strokeStyle = "#ff5a00";
    ctx.lineWidth = Math.max(2.4, w * 0.02);
    ctx.beginPath();
    ctx.moveTo(cx + (R - w * 0.14) * Math.cos(a), cy + (R - w * 0.14) * Math.sin(a));
    ctx.lineTo(cx + (R + w * 0.006) * Math.cos(a), cy + (R + w * 0.006) * Math.sin(a));
    ctx.stroke();
  }

  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillStyle = "#111111";
  ctx.font = `700 ${Math.max(16, w * 0.18)}px "Space Mono", monospace`;
  ctx.fillText(cfg.text, cx, cy - w * 0.02);
  ctx.fillStyle = "#6b6458";
  ctx.font = `700 ${Math.max(8, w * 0.055)}px "Inter", sans-serif`;
  ctx.fillText(cfg.unit, cx, cy + w * 0.12);
}

export function drawGauges(state) {
  const azCanvas = $("gauge-az");
  const elCanvas = $("gauge-el");
  if (!azCanvas || !elCanvas) return;
  const row = azCanvas.closest(".gauge-row");
  if (row && getComputedStyle(row).display === "none") return;

  const look = state.look;
  const targetAz = look?.az ?? 0;
  const targetEl = look?.el ?? -90;
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (reducedMotion || state.gAz == null) {
    state.gAz = targetAz;
    state.gEl = targetEl;
  } else {
    let dAz = ((targetAz - state.gAz + 540) % 360) - 180;
    state.gAz = (state.gAz + dAz * 0.14 + 360) % 360;
    state.gEl += (targetEl - state.gEl) * 0.14;
  }

  drawArcGauge(azCanvas, {
    value: state.gAz, min: 0, max: 360,
    text: look ? state.gAz.toFixed(0) + "°" : "—",
    unit: "AZIMUTH", color0: "#111111", color1: "#ff5a00"
  });
  drawArcGauge(elCanvas, {
    value: state.gEl, min: -90, max: 90,
    text: look ? state.gEl.toFixed(0) + "°" : "—",
    unit: "ELEVATION", color0: "#111111", color1: "#ff5a00"
  });
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

  ctx.strokeStyle = "#111111";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.stroke();

  for (let deg = 0; deg < 360; deg += 15) {
    const a = deg * Math.PI / 180;
    const inner = deg % 90 === 0 ? R - 10 : deg % 45 === 0 ? R - 7 : R - 4;
    ctx.strokeStyle = "#111111";
    ctx.lineWidth = deg % 90 === 0 ? 2 : 1;
    ctx.beginPath();
    ctx.moveTo(cx + inner * Math.sin(a), cy - inner * Math.cos(a));
    ctx.lineTo(cx + R * Math.sin(a), cy - R * Math.cos(a));
    ctx.stroke();
  }

  ctx.fillStyle = "#111111";
  ctx.font = "700 11px 'Space Mono', monospace";
  ctx.textAlign = "center";
  ctx.fillText("N", cx, cy - R + 18);

  const target = state.look?.az ?? 0;
  state.easeCompass?.(target);
  const a = (state.compassNeedle || target) * Math.PI / 180;

  ctx.strokeStyle = "#ff5a00";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + (R - 6) * Math.sin(a), cy - (R - 6) * Math.cos(a));
  ctx.stroke();

  if (state.heading != null) {
    const hdg = state.heading * Math.PI / 180;
    ctx.strokeStyle = "#ffe600";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + (R - 16) * Math.sin(hdg), cy - (R - 16) * Math.cos(hdg));
    ctx.stroke();
  }

  $("compass-read").textContent = state.heading != null
    ? `HEADING ${state.heading.toFixed(0)}° · TARGET ${cardinal(target)}`
    : `TARGET ${cardinal(target)} (${target.toFixed(0)}°)`;
}

export function drawTrack(state) {
  const canvas = $("ground-track");
  if (!canvas) return;
  const wrap = canvas.closest(".d4");
  if (wrap && getComputedStyle(wrap).display === "none") return;
  const { ctx, w, h } = sizeCanvas(canvas);
  
  ctx.fillStyle = "#e8e2d6";
  ctx.fillRect(0, 0, w, h);

  ctx.strokeStyle = "rgba(17, 17, 17, 0.18)";
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

  ctx.fillStyle = "#6b6458";
  ctx.font = "9px 'Space Mono', monospace";
  ctx.textAlign = "left";
  ctx.fillText("+90", 4, 12);
  ctx.fillText("-90", 4, h - 6);
  ctx.textAlign = "center";
  ctx.fillText("0", w / 2, h / 2 - 4);

  const proj = (lat, lon) => [(lon + 180) / 360 * w, (90 - lat) / 180 * h];
  const pts = state.track || [];

  if (pts.length > 1) {
    ctx.strokeStyle = "#111111";
    ctx.lineWidth = 1.5;
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
    ctx.fillStyle = "#ff5a00";
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  if (state.obs) {
    const [x, y] = proj(state.obs.lat, state.obs.lon);
    ctx.strokeStyle = "#111111";
    ctx.lineWidth = 2;
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
  const liveIss = state.targetId === "25544" && state.iss;
  const sgp4 = state.satrec ? sgp4Look(state.satrec, state.obs, new Date()) : null;

  if (liveIss) {
    const iss = state.iss;
    $("iss-lat").textContent = iss.latitude.toFixed(4) + "°";
    $("iss-lon").textContent = iss.longitude.toFixed(4) + "°";
    $("iss-alt").textContent = iss.altitude.toFixed(1) + " KM";
    $("iss-vel").textContent = iss.velocity.toFixed(0) + " KM/H";
    $("iss-vis").textContent = (iss.visibility || "").toUpperCase();
    $("iss-ts").textContent = new Date(iss.timestamp * 1000).toISOString();

    const look = lookAngles(state.obs, { lat: iss.latitude, lon: iss.longitude, altKm: iss.altitude });
    const sunAlt = sunAltitude(state.obs.lat, state.obs.lon, new Date());
    let eclipsed = iss.visibility === "eclipsed";
    let mag = sgp4?.mag ?? null;
    if (sgp4) eclipsed = sgp4.eclipsed;
    const label = eyeLabel({ el: look.el, eclipsed, sunAlt });
    state.look = { ...look, mag, label, eclipsed, source: "LIVE" };
    state.residual = issResidual(iss, sgp4);
  } else if (sgp4) {
    const label = eyeLabel({ el: sgp4.el, eclipsed: sgp4.eclipsed, sunAlt: sgp4.sunAlt });
    state.look = { az: sgp4.az, el: sgp4.el, range: sgp4.range, mag: sgp4.mag, label, eclipsed: sgp4.eclipsed, source: "SGP4" };
    state.residual = null;
    if ($("iss-lat")) {
      $("iss-lat").textContent = sgp4.lat.toFixed(4) + "°";
      $("iss-lon").textContent = sgp4.lon.toFixed(4) + "°";
      $("iss-alt").textContent = sgp4.altKm.toFixed(1) + " KM";
      $("iss-vel").textContent = "SGP4";
      $("iss-vis").textContent = sgp4.eclipsed ? "ECLIPSED" : "LIT";
      $("iss-ts").textContent = new Date().toISOString();
    }
  } else {
    return;
  }

  const look = state.look;
  setNum($("az"), look.az.toFixed(1) + "°");
  setNum($("el"), look.el.toFixed(1) + "°");
  setNum($("range"), look.range.toFixed(0) + " KM");
  setNum($("mag"), look.mag == null ? "—" : look.mag.toFixed(1) + " EST");
  $("face").textContent = faceCopy({ az: look.az, el: look.el, range: look.range, label: look.label });
  paintResidual(state);
  state.unit?.setLook({ az: look.az, el: look.el });
  const nowLock = look.el >= 10;
  if (nowLock && !state._wasLock) state.audio?.playLockAcquire();
  state._wasLock = nowLock;
}

function paintResidual(state) {
  const el = $("residual");
  const src = $("lock-src");
  if (src) src.textContent = state.look?.source === "LIVE" ? "Where The ISS At" : "SGP4";
  if (!el) return;
  const r = state.residual;
  if (!r) {
    el.textContent = state.look?.source === "SGP4" ? "No live GPS for this object. SGP4 only." : "—";
    el.dataset.grade = "";
    return;
  }
  el.textContent = `SGP4 residual ${r.km.toFixed(1)} km · ${r.grade}`;
  el.dataset.grade = r.grade.toLowerCase();
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
      li.dataset.idx = String(i + 1).padStart(3, "0");
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

function fillPassTable(tbody, upcoming, hourly, kp) {
  if (!tbody) return;
  tbody.innerHTML = "";
  upcoming.forEach((p) => {
    const wx = wxAt(hourly, p.maxT);
    const slice = wxSlice(hourly, p.maxT);
    const sc = scorePass(p, slice, kp);
    p.score = sc;
    const tr = document.createElement("tr");
    const eyeClass = p.eye === "NAKED-EYE" ? "eye-naked" : p.eye === "DAY" ? "eye-day" : "eye-ecl";
    if (sc.pct >= 70) tr.dataset.best = "1";
    tr.innerHTML = `
      <td>${p.aos <= Date.now() && p.los > Date.now() ? "IN VIEW NOW" : fmtTime(p.aos)}</td>
      <td>${fmtTime(p.maxT)}</td>
      <td>${fmtTime(p.los)}</td>
      <td>${p.maxEl.toFixed(0)}°</td>
      <td class="${eyeClass}">${p.eye}</td>
      <td>${wx.cls.toUpperCase()}</td>
      <td>${String(sc.pct).padStart(2, "0")}</td>`;
    tbody.appendChild(tr);
  });
}

export function paintPasses(state) {
  const body = $("pass-body");
  const manifest = $("manifest-body");
  const nextWhen = $("next-when");
  const nextMeta = $("next-meta");
  const note = $("manifest-note");
  const bestEl = $("best-window");

  if (state.tleError) {
    const msg = `<tr><td colspan="7">TLE sync error: ${state.tleError}</td></tr>`;
    body.innerHTML = msg;
    if (manifest) manifest.innerHTML = msg;
    nextWhen.textContent = "OFFLINE";
    nextMeta.textContent = state.targetId === "25544"
      ? "Direct ISS position may still be live."
      : "SGP4 catalog unread.";
    note.textContent = state.tleError;
    if (bestEl) bestEl.textContent = "—";
    return;
  }

  const passes = state.passes || [];
  if (!passes.length) {
    const msg = `<tr><td colspan="7">Zero 10° elevation passes in the next 36 hours for this position.</td></tr>`;
    body.innerHTML = msg;
    if (manifest) manifest.innerHTML = msg;
    nextWhen.textContent = "NONE (36H)";
    nextMeta.textContent = "SGP4 search complete.";
    note.textContent = "No passes >10° elevation in 36h.";
    if (bestEl) bestEl.textContent = "None in 36h.";
    return;
  }

  const upcoming = passes.filter((p) => p.los > Date.now());
  upcoming.forEach((p) => {
    p.score = scorePass(p, wxSlice(state.wx?.hourly, p.maxT), state.kp);
  });
  const n = upcoming[0] || passes[0];
  const best = [...upcoming].sort((a, b) => (b.score?.p || 0) - (a.score?.p || 0))[0] || n;
  const now = Date.now();
  const inView = n.aos <= now && n.los > now;
  const imminent = !inView && n.aos - now < 10 * 60 * 1000 && n.aos > now;

  $("next-pass").classList.toggle("is-imminent", imminent || inView);
  nextWhen.textContent = inView ? "IN VIEW NOW" : imminent ? "IMMINENT" : fmtTime(n.aos);
  nextMeta.textContent = `${n.eye} · peak ${n.maxEl.toFixed(0)}° · score ${n.score?.pct ?? "—"}`;
  if (bestEl) {
    bestEl.textContent = best === n
      ? `Best window is the next one (${best.score?.pct ?? "—"}).`
      : `Best in 36h: ${fmtTime(best.aos)} · score ${best.score?.pct} · ${best.eye} · ${best.maxEl.toFixed(0)}°.`;
  }

  fillPassTable(body, upcoming.slice(0, 12), state.wx?.hourly, state.kp);
  fillPassTable(manifest, upcoming.slice(0, 12), state.wx?.hourly, state.kp);
  note.textContent = `${upcoming.length} passes · Celestrak GP + SGP4 · scores are a logistic prior on live weather, not a forecast guarantee.`;

  maybeAlert(state, n, imminent, inView);
}

/* T-minus band: giant thin countdown to the next pass window,
   with an AOS→LOS scrubber that fills while the station is overhead. */
export function paintCountdown(state) {
  const elT = $("tminus");
  if (!elT) return;
  const fill = $("scrub-fill");
  const la = $("scrub-a");
  const ll = $("scrub-l");
  const fmt = (ms) => {
    const s = Math.max(0, Math.floor(ms / 1000));
    const hh = String(Math.floor(s / 3600)).padStart(2, "0");
    const mm = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
    const ss = String(s % 60).padStart(2, "0");
    return `${hh}:${mm}:${ss}`;
  };
  const upcoming = (state.passes || []).filter((p) => p.los > Date.now());
  if (!upcoming.length) {
    elT.textContent = "T\u2212 --:--:--";
    if (fill) fill.style.width = "0%";
    if (la) la.textContent = "AOS \u2014";
    if (ll) ll.textContent = "LOS \u2014";
    return;
  }
  const n = upcoming[0];
  const now = Date.now();
  if (la) la.textContent = "AOS " + new Date(n.aos).toISOString().slice(11, 16) + "Z";
  if (ll) ll.textContent = "LOS " + new Date(n.los).toISOString().slice(11, 16) + "Z";
  if (n.aos <= now) {
    elT.textContent = "T\u2212" + fmt(n.los - now);
    if (fill) fill.style.width = Math.min(100, ((now - n.aos) / (n.los - n.aos)) * 100).toFixed(1) + "%";
  } else {
    elT.textContent = "T\u2212" + fmt(n.aos - now);
    if (fill) fill.style.width = "0%";
  }
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
    cap.textContent = `RainViewer · ${when} · observer center`;
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
  if (state.targetId && state.targetId !== "25544") {
    state.issError = null;
    paintLock(state);
    paintFeed(state, "iss", "idle");
    return;
  }
  try {
    const got = await getIss();
    state.iss = got.data;
    state.issError = null;
    state.issAt = Date.now();
    paintLock(state);
    paintFeed(state, "iss", "live", state.issAt);
    state.audio?.playLockTick();
  } catch (e) {
    state.issError = e.message;
    paintFeed(state, "iss", "down");
    if (state.satrec) paintLock(state);
    else $("face").textContent = `FACE — ISS telemetry link offline (${e.message}).`;
  }
}

export async function loadTle(state) {
  try {
    await waitForSatellite();
    let catalog = [];
    try {
      const stations = await getStations();
      catalog = parseAllTles(stations.data);
      paintFeed(state, "tle", "live");
    } catch {
      const one = await getTle(state.targetId || "25544");
      catalog = parseAllTles(one.data);
      paintFeed(state, "tle", "live");
    }
    state.catalog = catalog;
    fillSatSelect(state);
    writeShare(state);
    const id = state.targetId || "25544";
    const row = catalog.find((s) => s.norad === id) || catalog.find((s) => s.norad === "25544") || catalog[0];
    if (!row) throw new Error("target not in TLE set");
    state.targetId = row.norad;
    state.targetName = row.name;
    state.satrec = window.satellite.twoline2satrec(row.l1, row.l2);
    state.tleError = null;
    state.tleAt = Date.now();
    const gen = ++state.passGen;
    const body = $("pass-body");
    if (body && !state.passes?.length) {
      body.innerHTML = `<tr><td colspan="7">Computing intersections…</td></tr>`;
    }
    const passes = await findPassesAsync(state.satrec, state.obs, 36, {
      shouldAbort: () => state.passGen !== gen
    });
    if (passes == null) return;
    state.passes = passes;
    state.track = groundTrack(state.satrec, state.obs);
    paintPasses(state);
    if (state.wx) paintWeather(state);
    paintLock(state);
    state.drawTrack?.();
    const note = $("mod-02-note");
    if (note) note.textContent = `${row.name} ${row.norad}`;
  } catch (e) {
    state.tleError = `Celestrak GP: ${e.message}`;
    paintFeed(state, "tle", "down");
    paintPasses(state);
  }
}

export async function loadWeather(state) {
  try {
    const { lat, lon } = state.obs;
    const got = await getWeather(lat, lon);
    state.wx = got.data;
    state.wxError = null;
    paintWeather(state);
    paintPasses(state);
    paintFeed(state, "wx", "live");
  } catch (e) {
    state.wxError = e.message;
    paintWeather(state);
    paintFeed(state, "wx", "down");
  }
}

export async function loadRadar(state) {
  try {
    const maps = (await getRadarIndex()).data;
    const frames = maps?.radar?.past || [];
    if (!frames.length) {
      state.radarUrl = null;
      state.radarError = "RainViewer past frames empty.";
      paintRadar(state);
      paintFeed(state, "radar", "down");
      return;
    }
    const last = frames[frames.length - 1];
    const { x, y, z } = tileXY(state.obs.lat, state.obs.lon, 6);
    state.radarUrl = `${maps.host}${last.path}/256/${z}/${x}/${y}/2/1_1.png`;
    state.radarTime = last.time;
    state.radarError = null;
    paintRadar(state);
    paintFeed(state, "radar", "live");
  } catch (e) {
    state.radarError = e.message;
    state.radarUrl = null;
    paintRadar(state);
    paintFeed(state, "radar", "down");
  }
}

export async function loadKp(state) {
  try {
    const rows = (await getKp()).data;
    const last = rows[rows.length - 1];
    state.kp = last?.kp_index ?? last?.estimated_kp ?? null;
    state.kpError = null;
    paintKp(state);
    paintFeed(state, "kp", "live");
  } catch (e) {
    state.kpError = e.message;
    paintKp(state);
    paintFeed(state, "kp", "down");
  }
}

export async function loadStarship(state) {
  const el = $("starship-status");
  const ro = $("starship-readout");
  try {
    const got = await getStarship();
    if (got.status === 404 || got.data == null) {
      state.starship = null;
      state.starshipError = null;
      paintStarship(state);
      return;
    }
    const rows = got.data;
    state.starship = Array.isArray(rows) && rows.length ? rows[0] : null;
    state.starshipError = null;
    paintStarship(state);
  } catch (e) {
    state.starshipError = e.message;
    paintStarship(state);
  }
}

function fillSatSelect(state) {
  const sel = $("sat-select");
  if (!sel || !state.catalog?.length) return;
  const cur = state.targetId || "25544";
  sel.innerHTML = state.catalog.map((s) => {
    const selAttr = s.norad === cur ? " selected" : "";
    return `<option value="${s.norad}"${selAttr}>${s.name} · ${s.norad}</option>`;
  }).join("");
}

export function paintFeed(state, id, status, at) {
  const li = document.querySelector(`[data-feed="${id}"]`);
  if (!li) return;
  li.dataset.status = status;
  const label = li.querySelector(".feed-st");
  if (label) label.textContent = status;
  if (at) li.dataset.at = String(at);
}

export function markIssAge(state) {
  if (!state.issAt || state.targetId !== "25544") return;
  const age = Date.now() - state.issAt;
  if (age > 20_000) paintFeed(state, "iss", "stale", state.issAt);
}

function maybeAlert(state, n, imminent, inView) {
  if (!state.alertsOn) return;
  if (!imminent && !inView) return;
  if ((n.score?.pct ?? 0) < 55) return;
  if (state._alerted === n.aos) return;
  state._alerted = n.aos;
  try {
    if (typeof Notification !== "undefined" && Notification.permission === "granted") {
      new Notification("OP-01 pass", {
        body: `${n.eye} · score ${n.score.pct} · peak ${n.maxEl.toFixed(0)}°`,
        tag: "op-01-pass"
      });
    }
  } catch { /* ignore */ }
}

export function bindTarget(state) {
  const sel = $("sat-select");
  if (!sel) return;
  const saved = localStorage.getItem("op-sat");
  if (saved) state.targetId = saved;
  sel.addEventListener("change", () => {
    state.targetId = sel.value;
    localStorage.setItem("op-sat", sel.value);
    writeShare(state);
    const mid = $("mast-target");
    if (mid) mid.textContent = `${sel.selectedOptions[0]?.textContent || sel.value} · public ephemeris · no account`;
    loadTle(state);
    loadIss(state);
  });
}

export function bindSpeak(state) {
  $("btn-speak")?.addEventListener("click", () => {
    const t = $("face")?.textContent;
    if (!t || !window.speechSynthesis) return;
    const u = new SpeechSynthesisUtterance(t);
    u.rate = 0.95;
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
    state.audio?.playModeClick();
  });
}

export function bindAlert(state) {
  const btn = $("btn-alert");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    if (!("Notification" in window)) {
      btn.textContent = "No alerts";
      return;
    }
    const perm = await Notification.requestPermission();
    state.alertsOn = perm === "granted";
    btn.setAttribute("aria-pressed", state.alertsOn ? "true" : "false");
    btn.textContent = state.alertsOn ? "Alerts on" : "Alerts";
  });
}

export function bindShare(state) {
  $("btn-share")?.addEventListener("click", async () => {
    writeShare(state);
    const url = location.href;
    try {
      await navigator.clipboard.writeText(url);
      const btn = $("btn-share");
      if (btn) {
        btn.textContent = "Copied";
        setTimeout(() => { btn.textContent = "Copy link"; }, 1400);
      }
    } catch {
      window.prompt("Copy this observer link", url);
    }
  });
}

function icsStamp(ms) {
  return new Date(ms).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

export function bindIcs(state) {
  $("btn-ics")?.addEventListener("click", () => {
    const n = (state.passes || []).filter((p) => p.los > Date.now())[0];
    if (!n) return;
    const name = (state.targetName || "ISS").replace(/[,;]/g, " ");
    const body = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//OP-01 Orbital Prime//EN",
      "BEGIN:VEVENT",
      `UID:op01-${state.targetId || "25544"}-${n.aos}@orbital-prime`,
      `DTSTAMP:${icsStamp(Date.now())}`,
      `DTSTART:${icsStamp(n.aos)}`,
      `DTEND:${icsStamp(n.los)}`,
      `SUMMARY:${name} pass · ${n.eye} · score ${n.score?.pct ?? "—"}`,
      `DESCRIPTION:Peak elevation ${n.maxEl.toFixed(0)}°. FACE from OP-01. Public SGP4. Not a guarantee.`,
      "END:VEVENT",
      "END:VCALENDAR"
    ].join("\r\n");
    const blob = new Blob([body], { type: "text/calendar" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `op01-pass-${n.aos}.ics`;
    a.click();
    URL.revokeObjectURL(a.href);
  });
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
      msg.textContent = "Camera on. FACE still authoritative.";
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
    
    if (state.satrec && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
      ctx.strokeStyle = "#ffe600";
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i <= 8; i++) {
        const s = sgp4Look(state.satrec, state.obs, new Date(Date.now() + i * 30 * 1000));
        if (!s) continue;
        const p = project(s, heading, w, h);
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
    }

    const p = project(look, heading, w, h);
    ctx.strokeStyle = "#ff5a00";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 16, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = "#ffe600";
    ctx.font = "700 12px 'Space Mono', monospace";
    ctx.fillText(`EL ${look.el.toFixed(0)}°  ΔAZ ${(((look.az - heading + 540) % 360) - 180).toFixed(0)}°`, 12, 22);
  };
}

export function bindResize(state) {
  const ro = new ResizeObserver(() => {
    state.drawPlot?.();
    state.drawTrack?.();
    drawCompass(state);
    drawGauges(state);
  });
  ["sky-plot", "ground-track", "gauge-az"].forEach((id) => {
    const el = $(id)?.parentElement;
    if (el) ro.observe(el);
  });
}
