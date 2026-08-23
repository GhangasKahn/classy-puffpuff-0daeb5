/* SGP4 pass search off the UI thread.
   satellite.js is a UMD build — do not import it as an ES module.
   Fetch + Function boots it onto globalThis the same way the page script tag does. */

import { findPasses, getSatellite } from "./astro.js";
import { bootSatelliteUmd } from "./sat-boot.js";

let satBoot = null;

function ensureSat() {
  if (getSatellite()?.twoline2satrec) return Promise.resolve(getSatellite());
  if (!satBoot) {
    satBoot = fetch(new URL("../vendor/satellite.min.js", import.meta.url))
      .then((r) => {
        if (!r.ok) throw new Error("satellite.js HTTP " + r.status);
        return r.text();
      })
      .then(bootSatelliteUmd)
      .catch((err) => {
        satBoot = null;
        throw err;
      });
  }
  return satBoot;
}

self.onmessage = async (e) => {
  const { l1, l2, obs, hours } = e.data || {};
  try {
    const sat = await ensureSat();
    if (!l1 || !l2 || !obs) throw new Error("TLE or observer missing");
    const satrec = sat.twoline2satrec(l1, l2);
    const passes = findPasses(satrec, obs, hours || 36).map((p) => ({
      aos: p.aos,
      los: p.los,
      maxT: p.maxT,
      maxEl: p.maxEl,
      mag: p.mag,
      eye: p.eye,
      eclipsed: p.eclipsed,
      sunAlt: p.sunAlt,
      aosAz: p.samples?.[0]?.az
    }));
    self.postMessage({ ok: true, passes });
  } catch (err) {
    self.postMessage({ ok: false, error: err.message || String(err) });
  }
};
