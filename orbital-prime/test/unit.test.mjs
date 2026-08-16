import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { encoderAngles, isLocked } from "../js/gl/unit.js";
import { findPassesAsync, parseShareQuery } from "../js/astro.js";

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
