/* Boot the vendored satellite.js UMD onto globalThis.
   Used by the page (script tag) equivalently, and by the pass worker
   via fetch + this function. Do not `import` the UMD as an ES module. */

export function bootSatelliteUmd(src) {
  if (typeof src !== "string" || !src.includes("twoline2satrec")) {
    throw new Error("satellite.js source missing");
  }
  const run = new Function(src);
  run();
  const sat = globalThis.satellite;
  if (!sat?.twoline2satrec) throw new Error("satellite.js failed to boot");
  return sat;
}
