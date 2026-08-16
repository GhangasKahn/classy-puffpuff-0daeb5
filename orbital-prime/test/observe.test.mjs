import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { validateObserveInput } from "../js/observe.js";

describe("validateObserveInput", () => {
  it("accepts Buffalo ISS", () => {
    const v = validateObserveInput({ lat: 42.8864, lon: -78.8784, sat: "25544" });
    assert.equal(v.ok, true);
    assert.equal(v.input.sat, "25544");
    assert.equal(v.input.hours, 36);
  });

  it("rejects a missing latitude", () => {
    const v = validateObserveInput({ lon: -78.8784 });
    assert.equal(v.ok, false);
  });

  it("rejects Starlink-shaped junk as sat ids that are not NORAD numbers", () => {
    const v = validateObserveInput({ lat: 0, lon: 0, sat: "starlink" });
    assert.equal(v.ok, false);
  });

  it("rejects hours outside 1–72", () => {
    assert.equal(validateObserveInput({ lat: 1, lon: 1, hours: 0 }).ok, false);
    assert.equal(validateObserveInput({ lat: 1, lon: 1, hours: 100 }).ok, false);
  });
});
