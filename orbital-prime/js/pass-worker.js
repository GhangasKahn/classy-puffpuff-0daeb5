/* SGP4 pass search off the UI thread.
   Same findPasses as astro.js. Slims samples so postMessage stays small. */

import "../vendor/satellite.min.js";
import { findPasses } from "./astro.js";

self.onmessage = (e) => {
  const { l1, l2, obs, hours } = e.data || {};
  try {
    const sat = globalThis.satellite;
    if (!sat?.twoline2satrec) throw new Error("satellite.js missing in worker");
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
