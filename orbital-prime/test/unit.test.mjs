import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { encoderAngles, isLocked } from "../js/gl/unit.js";
import { findPassesAsync, parseShareQuery } from "../js/astro.js";
import { bootSatelliteUmd } from "../js/sat-boot.js";

const here = dirname(fileURLToPath(import.meta.url));
const workerSrc = readFileSync(join(here, "../js/pass-worker.js"), "utf8");
const umdSrc = readFileSync(join(here, "../vendor/satellite.min.js"), "utf8");

describe("encoderAngles", () => {
  it("wraps negative azimuth into 0..360", () => {
    const e = encoderAngles(-90, 0);
    assert.equal(e.az, 270);
  });

  it("maps elevation 0 to no wedge and 90 to 270 degrees of pie", () => {
    assert.equal(encoderAngles(0, 0).wedgeRad, 0);
    assert.ok(Math.abs(encoderAngles(0, 90).wedgeRad - Math.PI * 1.5) < 1e-9);
  });

  it("locks at 10 degrees elevation, not below", () => {
    assert.equal(isLocked(9.9), false);
    assert.equal(isLocked(10), true);
    assert.equal(encoderAngles(12, 45).locked, true);
  });

  it("does not invent a look — NaN elevation is 0", () => {
    const e = encoderAngles(10, Number.NaN);
    assert.equal(e.el, 0);
    assert.equal(e.locked, false);
  });
});

describe("findPassesAsync", () => {
  it("is async and aborts before SGP4 when asked", async () => {
    assert.equal(typeof findPassesAsync, "function");
    const out = await findPassesAsync(null, { lat: 0, lon: 0 }, 36, {
      shouldAbort: () => true
    });
    assert.equal(out, null);
  });
});

describe("parseShareQuery", () => {
  it("does not treat a bare URL as the Gulf of Guinea", () => {
    assert.equal(parseShareQuery(""), null);
    assert.equal(parseShareQuery("/"), null);
    assert.equal(parseShareQuery("?sat=25544"), null);
  });

  it("accepts explicit 0,0 when both params are present", () => {
    const s = parseShareQuery("?lat=0&lon=0&sat=25544");
    assert.equal(s.lat, 0);
    assert.equal(s.lon, 0);
    assert.equal(s.sat, "25544");
  });

  it("rejects out-of-range coordinates", () => {
    assert.equal(parseShareQuery("?lat=91&lon=0"), null);
    assert.equal(parseShareQuery("?lat=0&lon=181"), null);
  });
});

describe("pass worker satellite boot", () => {
  it("does not import the UMD as an ES module", () => {
    assert.doesNotMatch(workerSrc, /import\s+["']\.\.\/vendor\/satellite/);
    assert.match(workerSrc, /bootSatelliteUmd/);
  });

  it("boots satellite.js onto globalThis via Function", () => {
    const sat = bootSatelliteUmd(umdSrc);
    const rec = sat.twoline2satrec(
      "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927",
      "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
    );
    const pv = sat.propagate(rec, new Date(Date.UTC(2008, 8, 20, 12, 25, 40)));
    assert.ok(pv.position);
    assert.equal(typeof pv.position.x, "number");
  });
});
