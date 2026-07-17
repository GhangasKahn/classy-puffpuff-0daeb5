"use strict";
/* ============================================================
   AEGIS AIR — SAT RECON module.
   Open-source satellite imagery from NASA GIBS (Terra/MODIS,
   Suomi-NPP & NOAA-20/VIIRS): daily true-color + burn bands +
   aerosol optical depth. Date scrub, pass animation, and a
   CAPTURE routine that composes visible tiles into a stamped
   PNG for download. No API key.
   ============================================================ */

const AegisSat = (() => {
  const GIBS = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best";
  const DAYS = 10;                 // scrubbable window
  const LATENCY_H = 48;            // imagery reliably complete ~2 days behind now
  const BLANK = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==";

  const S = {
    map: null, base: null, aod: null, fireLayer: null,
    layerId: "MODIS_Terra_CorrectedReflectance_TrueColor",
    dates: [], dateIdx: DAYS - 1,
    showAod: true, showFires: true,
    playTimer: null,
    getFires: () => [],
    onLog: () => {},
  };

  function buildDates() {
    const newest = new Date(Date.now() - LATENCY_H * 3600e3);
    S.dates = Array.from({ length: DAYS }, (_, i) => {
      const d = new Date(newest.getTime() - (DAYS - 1 - i) * 86400e3);
      return d.toISOString().slice(0, 10);
    });
  }
  const curDate = () => S.dates[S.dateIdx];

  function tileUrl(layer, date, maxLevel) {
    return `${GIBS}/${layer}/default/${date}/GoogleMapsCompatible_Level${maxLevel}/{z}/{y}/{x}.${layer.includes("AOD") ? "png" : "jpg"}`;
  }

  function makeBase() {
    if (S.base) S.map.removeLayer(S.base);
    S.base = L.tileLayer(tileUrl(S.layerId, curDate(), 9), {
      maxNativeZoom: 9, maxZoom: 12, crossOrigin: "anonymous", errorTileUrl: BLANK,
      attribution: 'NASA <a href="https://worldview.earthdata.nasa.gov">GIBS/Worldview</a>',
    }).addTo(S.map);
  }
  function makeAod() {
    if (S.aod) { S.map.removeLayer(S.aod); S.aod = null; }
    if (!S.showAod) return;
    S.aod = L.tileLayer(tileUrl("MODIS_Combined_Value_Added_AOD", curDate(), 6), {
      maxNativeZoom: 6, maxZoom: 12, opacity: 0.38, crossOrigin: "anonymous", errorTileUrl: BLANK,
    }).addTo(S.map);
  }
  function makeFires() {
    if (!S.map) return;
    if (S.fireLayer) { S.map.removeLayer(S.fireLayer); S.fireLayer = null; }
    if (!S.showFires) return;
    const g = L.layerGroup();
    for (const f of S.getFires().slice(0, 250)) {
      L.marker([f.lat, f.lon], {
        icon: L.divIcon({ className: "fire-dot", iconSize: [7, 7] }),
      }).bindTooltip(`${f.title} · ${Math.round(f.dist)} km`, { className: "globe-tip" }).addTo(g);
    }
    S.fireLayer = g.addTo(S.map);
  }

  function refresh() {
    makeBase(); makeAod(); makeFires();
    document.getElementById("satDate").textContent = curDate() + (S.dateIdx === DAYS - 1 ? " · LATEST" : "");
    probeAvailability();
  }

  /* probe one mid-zoom tile near map center; warn if this satellite/date has no imagery yet */
  let probeSeq = 0;
  async function probeAvailability() {
    const seq = ++probeSeq;
    const c = S.map.getCenter();
    const n = 2 ** 5;
    const x = Math.floor((c.lng + 180) / 360 * n);
    const y = Math.floor((1 - Math.log(Math.tan(c.lat * Math.PI / 180) + 1 / Math.cos(c.lat * Math.PI / 180)) / Math.PI) / 2 * n);
    try {
      const r = await fetch(`${GIBS}/${S.layerId}/default/${curDate()}/GoogleMapsCompatible_Level9/5/${y}/${x}.jpg`, { method: "HEAD" });
      if (seq !== probeSeq) return;
      if (!r.ok) S.onLog(`SAT NOTICE — ${S.layerId.split("_")[0]} HAS NO PROCESSED IMAGERY FOR ${curDate()} HERE. TRY MODIS TERRA OR AN EARLIER DATE.`, "warn");
    } catch { /* offline — tiles will fall back to cache */ }
  }

  /* ---------- CAPTURE: compose visible tiles → stamped PNG ---------- */
  async function capture() {
    const map = S.map, zoom = Math.min(map.getZoom(), 9);
    const b = map.getBounds();
    const t = (lat, lon, z) => {
      const n = 2 ** z;
      return {
        x: Math.floor((lon + 180) / 360 * n),
        y: Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * n),
      };
    };
    const tl = t(b.getNorth(), b.getWest(), zoom), br = t(b.getSouth(), b.getEast(), zoom);
    const cols = Math.min(br.x - tl.x + 1, 6), rows = Math.min(br.y - tl.y + 1, 6);
    const T = 256, W = cols * T, H = rows * T + 46;
    const cv = document.createElement("canvas");
    cv.width = W; cv.height = H;
    const ctx = cv.getContext("2d");
    ctx.fillStyle = "#04070d"; ctx.fillRect(0, 0, W, H);

    S.onLog(`SAT CAPTURE — COMPOSING ${cols}×${rows} TILES @ Z${zoom}`);
    const jobs = [];
    const layers = [[S.layerId, 9, "jpg"], ...(S.showAod ? [["MODIS_Combined_Value_Added_AOD", 6, "png"]] : [])];
    for (const [layer, maxL, ext] of layers) {
      const z = Math.min(zoom, maxL);
      const scale = 2 ** (zoom - z);
      for (let cx = 0; cx < cols; cx++) for (let cy = 0; cy < rows; cy++) {
        const gx = tl.x + cx, gy = tl.y + cy;
        const url = `${GIBS}/${layer}/default/${curDate()}/GoogleMapsCompatible_Level${maxL}/${z}/${Math.floor(gy / scale)}/${Math.floor(gx / scale)}.${ext}`;
        jobs.push(
          fetch(url).then(r => r.ok ? r.blob() : null).then(bl => bl ? createImageBitmap(bl) : null)
            .then(img => {
              if (!img) return;
              const subSize = T / scale;
              const sx = (gx % scale) * subSize, sy = (gy % scale) * subSize;
              ctx.globalAlpha = layer.includes("AOD") ? 0.55 : 1;
              ctx.drawImage(img, sx, sy, subSize, subSize, cx * T, cy * T, T, T);
              ctx.globalAlpha = 1;
            }).catch(() => {})
        );
      }
    }
    await Promise.all(jobs);

    // metadata stamp
    ctx.fillStyle = "rgba(4,7,13,0.92)";
    ctx.fillRect(0, H - 46, W, 46);
    ctx.fillStyle = "#2ee6ff";
    ctx.font = "600 12px 'IBM Plex Mono', monospace";
    ctx.fillText(`◤ AEGIS SAT RECON — ${S.layerId.replace(/_/g, " ")}`, 10, H - 28);
    ctx.fillStyle = "#93a4c4";
    ctx.font = "10px 'IBM Plex Mono', monospace";
    const c = map.getCenter();
    ctx.fillText(`${curDate()} · CTR ${c.lat.toFixed(3)},${c.lng.toFixed(3)} · Z${zoom} · NASA GIBS/WORLDVIEW · OPEN DATA`, 10, H - 12);

    const a = document.createElement("a");
    a.href = cv.toDataURL("image/png");
    a.download = `aegis-satcap-${curDate()}-z${zoom}.png`;
    a.click();
    S.onLog("SAT CAPTURE COMPLETE — PNG DOWNLOADED", "ok");
  }

  /* ---------- init ---------- */
  function init({ center, getFires, onLog }) {
    if (S.map) return;
    S.getFires = getFires; S.onLog = onLog;
    buildDates();
    S.map = L.map("satmap", { zoomControl: true, worldCopyJump: true }).setView(center, 6);
    refresh();

    document.getElementById("satLayer").addEventListener("change", (e) => {
      S.layerId = e.target.value; refresh();
      onLog(`SAT LAYER — ${S.layerId}`);
    });
    document.getElementById("btnAod").addEventListener("click", (e) => {
      S.showAod = !S.showAod; e.target.classList.toggle("on", S.showAod); makeAod();
    });
    document.getElementById("btnFireOv").addEventListener("click", (e) => {
      S.showFires = !S.showFires; e.target.classList.toggle("on", S.showFires); makeFires();
    });
    document.getElementById("btnCapture").addEventListener("click", () => capture().catch(() => onLog("SAT CAPTURE FAILED", "err")));

    const slider = document.getElementById("satSlider");
    slider.max = DAYS - 1; slider.value = DAYS - 1;
    slider.addEventListener("input", () => { S.dateIdx = Number(slider.value); refresh(); });

    document.getElementById("btnSatPlay").addEventListener("click", (e) => {
      if (S.playTimer) { clearInterval(S.playTimer); S.playTimer = null; e.target.textContent = "▶"; return; }
      e.target.textContent = "■";
      onLog("SAT PASS REPLAY — LAST " + DAYS + " DAYS");
      let i = 0;
      S.playTimer = setInterval(() => {
        S.dateIdx = i % DAYS; slider.value = S.dateIdx; refresh();
        if (++i > DAYS) { clearInterval(S.playTimer); S.playTimer = null; e.target.textContent = "▶"; S.dateIdx = DAYS - 1; slider.value = S.dateIdx; refresh(); }
      }, 900);
    });
  }

  function invalidate() { S.map && S.map.invalidateSize(); }
  function recenter(lat, lon) { S.map && S.map.setView([lat, lon], Math.max(S.map.getZoom(), 6)); makeFires(); }
  function redrawFires() { makeFires(); }

  return { init, invalidate, recenter, redrawFires };
})();
