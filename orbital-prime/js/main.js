import { BUFFALO } from "./astro.js";
import { initMotion, listMotionListeners } from "./motion.js";
import {
  bindAr, bindDepth, bindHeading, bindLocation, bindResize, drawCompass,
  drawSkyPlot, drawTrack, loadIss, loadKp, loadRadar, loadStarship, loadTle,
  loadWeather, paintLock
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
  arOn: false
};

initMotion(state);
state.drawPlot = () => {
  drawSkyPlot(state);
  drawCompass(state);
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
};

refreshAll();
setInterval(() => loadIss(state).then(() => { state.drawPlot(); state.drawTrack(); }), 5000);
setInterval(() => { loadWeather(state); loadRadar(state); }, 10 * 60 * 1000);
setInterval(() => loadKp(state), 5 * 60 * 1000);
setInterval(() => { $clock(); }, 1000);

function $clock() {
  const el = document.getElementById("clock");
  if (el) el.textContent = new Date().toISOString().replace("T", " ").slice(0, 19) + " Z";
}

console.info("Orbital Prime motion map", listMotionListeners());
