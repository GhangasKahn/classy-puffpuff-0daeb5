import { BUFFALO } from "./astro.js?v=4";
import { ClickEngine } from "./audio.js?v=4";
import { initMotion, listMotionListeners } from "./motion.js?v=4";
import {
  bindAr, bindAlert, bindDepth, bindHeading, bindIcs, bindLocation, bindResize,
  bindShare, bindSpeak, bindTarget, drawCompass, drawGauges, drawSkyPlot, drawTrack,
  loadIss, loadKp, loadRadar, loadStarship, loadTle, loadWeather, markIssAge,
  paintCountdown, paintLock, writeShare
} from "./render.js?v=4";

const state = {
  obs: { ...BUFFALO },
  targetId: "25544",
  targetName: "ISS (ZARYA)",
  iss: null,
  satrec: null,
  catalog: [],
  passes: [],
  track: [],
  wx: null,
  look: null,
  heading: null,
  sweep: 0,
  compassNeedle: 0,
  arOn: false,
  alertsOn: false,
  audio: new ClickEngine()
};

const audioBtn = document.getElementById("btn-audio");
if (audioBtn) {
  audioBtn.setAttribute("aria-pressed", "false");
  audioBtn.addEventListener("click", () => {
    state.audio.muted = !state.audio.muted;
    audioBtn.classList.toggle("active", !state.audio.muted);
    audioBtn.setAttribute("aria-pressed", state.audio.muted ? "false" : "true");
    audioBtn.textContent = state.audio.muted ? "Audio" : "Audio on";
    if (!state.audio.muted) state.audio.playModeClick();
  });
}

document.querySelectorAll(".dock-item").forEach((item) => {
  item.addEventListener("click", () => {
    document.querySelectorAll(".dock-item").forEach((d) => d.classList.remove("active"));
    item.classList.add("active");
    state.audio?.playModeClick();
    const target = item.dataset.target;
    if (target === "#physics" || target === "#ar") {
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
bindTarget(state);
bindSpeak(state);
bindAlert(state);
bindShare(state);
bindIcs(state);
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
  writeShare(state);
  loadTle(state);
  loadWeather(state);
  loadRadar(state);
  if (state.iss || state.satrec) paintLock(state);
  state.drawPlot();
  state.drawTrack();
  state.audio?.playModeClick();
};

refreshAll();

setInterval(() => {
  if (document.hidden) return;
  loadIss(state).then(() => {
    markIssAge(state);
    state.drawPlot();
    state.drawTrack();
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

console.info("OP-01 motion", listMotionListeners());
