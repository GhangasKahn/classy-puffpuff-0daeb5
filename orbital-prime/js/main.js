import { BUFFALO } from "./astro.js";
import { initMotion, listMotionListeners } from "./motion.js";
import { SingularityField, CyberAudioEngine } from "./singularity.js";
import {
  bindAr, bindDepth, bindHeading, bindLocation, bindResize, drawCompass,
  drawGauges, drawSkyPlot, drawTrack, loadIss, loadKp, loadRadar,
  loadStarship, loadTle, loadWeather, paintCountdown, paintLock
} from "./render.js";

const state = {
  obs: { ...BUFFALO },
  iss: null,
  satrec: null,
  passes: [],
  track: [],
  wx: null,
  look: null,
  heading: null,
  sweep: 0,
  compassNeedle: 0,
  arOn: false,
  singularity: null,
  audio: new CyberAudioEngine()
};

// Initialize interactive background Singularity / Relativistic Plasma Engine
const singularityCanvas = document.getElementById("singularity-canvas");
if (singularityCanvas) {
  state.singularity = new SingularityField(singularityCanvas);
}

// Audio Engine Toggle
const audioBtn = document.getElementById("btn-audio");
if (audioBtn) {
  audioBtn.addEventListener("click", () => {
    state.audio.muted = !state.audio.muted;
    audioBtn.classList.toggle("active", !state.audio.muted);
    const icon = document.getElementById("audio-icon");
    if (icon) icon.textContent = state.audio.muted ? "🔇" : "🔊";
    if (!state.audio.muted) state.audio.playModeClick();
  });
}

// Pulse Plasma button
const pulseBtn = document.getElementById("btn-pulse-warp");
if (pulseBtn) {
  pulseBtn.addEventListener("click", () => {
    state.singularity?.pulse();
    state.audio?.playLockTick();
  });
}

// Mobile Bottom Quick-Dock Navigation
document.querySelectorAll(".dock-item").forEach((item) => {
  item.addEventListener("click", () => {
    document.querySelectorAll(".dock-item").forEach((d) => d.classList.remove("active"));
    item.classList.add("active");
    state.audio?.playModeClick();
    const target = item.dataset.target;
    if (target === "#physics" || target === "#ar") {
      // Auto upgrade depth if navigating to deep sections
      document.body.dataset.depth = "4";
      document.querySelectorAll(".depth-btn").forEach((b) => {
        b.setAttribute("aria-checked", b.dataset.depth === "4" ? "true" : "false");
      });
    }
    const targetEl = document.querySelector(target);
    if (targetEl) {
      targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

// Scroll-synced dock highlighting (music-app pattern: the dock always knows where you are)
const dockSections = [
  [document.querySelector(".hero"), "#top"],
  [document.getElementById("cluster"), "#cluster"],
  [document.getElementById("physics"), "#physics"],
  [document.getElementById("ar"), "#ar"]
].filter(([el]) => el);

const dockIo = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    const hit = dockSections.find(([el]) => el === e.target);
    if (!hit) continue;
    document.querySelectorAll(".dock-item").forEach((d) => {
      d.classList.toggle("active", d.dataset.target === hit[1]);
    });
  }
}, { rootMargin: "-35% 0px -55% 0px" });
dockSections.forEach(([el]) => dockIo.observe(el));

// PWA: offline shell + installability (HTTPS / localhost only)
if ("serviceWorker" in navigator && (location.protocol === "https:" || ["localhost", "127.0.0.1"].includes(location.hostname))) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("service-worker.js").catch(() => {});
  });
}

initMotion(state);

state.drawPlot = () => {
  drawSkyPlot(state);
  drawCompass(state);
  drawGauges(state);
};
state.drawTrack = () => drawTrack(state);

bindDepth(state);
bindLocation(state);
bindHeading(state);
bindAr(state);
bindResize(state);

async function refreshAll() {
  await Promise.all([
    loadIss(state),
    loadTle(state),
    loadWeather(state),
    loadRadar(state),
    loadKp(state),
    loadStarship(state)
  ]);
  state.drawPlot();
  state.drawTrack();
}

state.onLocation = () => {
  loadTle(state);
  loadWeather(state);
  loadRadar(state);
  if (state.iss) paintLock(state);
  state.drawPlot();
  state.drawTrack();
  state.audio?.playModeClick();
};

refreshAll();

// Live Telemetry Loops
setInterval(() => {
  if (document.hidden) return;
  loadIss(state).then(() => {
    state.drawPlot();
    state.drawTrack();
    if (state.look) {
      state.singularity?.setLook(state.look.az, state.look.el);
    }
  });
}, 4000);

setInterval(() => {
  if (document.hidden) return;
  loadWeather(state);
  loadRadar(state);
}, 10 * 60 * 1000);

setInterval(() => {
  if (document.hidden) return;
  loadKp(state);
}, 5 * 60 * 1000);

setInterval(() => {
  $clock();
  paintCountdown(state);
}, 1000);

function $clock() {
  const el = document.getElementById("clock");
  if (el) el.textContent = new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC";
}

console.info("ORBITAL PRIME // BRUTALIST MOTION MAP", listMotionListeners());
