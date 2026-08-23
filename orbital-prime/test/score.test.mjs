import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { haversineKm, scorePass, sigmoid } from "../js/score.js";

describe("sigmoid", () => {
  it("is 0.5 at 0", () => assert.equal(sigmoid(0), 0.5));
  it("saturates", () => {
    assert.equal(sigmoid(80), 1);
    assert.equal(sigmoid(-80), 0);
  });
});

describe("scorePass", () => {
  it("scores a high naked-eye pass under clear dry air above a day eclipsed pass", () => {
    const good = scorePass(
      { maxEl: 70, mag: -1.5, eye: "NAKED-EYE" },
      { cloud: 10, precip: 0, vis: 20000 },
      2
    );
    const bad = scorePass(
      { maxEl: 12, mag: 3.5, eye: "ECLIPSED", eclipsed: true },
      { cloud: 95, precip: 4, vis: 1000 },
      8
    );
    assert.ok(good.p > 0.7, `good ${good.pct}`);
    assert.ok(bad.p < 0.25, `bad ${bad.pct}`);
    assert.ok(good.pct > bad.pct);
  });

  it("does not invent weather — missing cloud stays 0.5 clear", () => {
    const s = scorePass({ maxEl: 40, mag: 0, eye: "NAKED-EYE" }, {});
    assert.equal(s.features.clear, 0.5);
    assert.equal(s.features.visNorm, 0.5);
  });
});

describe("haversineKm", () => {
  it("is ~0 for the same point", () => {
    assert.ok(haversineKm(42.8864, -78.8784, 42.8864, -78.8784) < 0.01);
  });
  it("Buffalo to NYC is hundreds of km, not tens", () => {
    const km = haversineKm(42.8864, -78.8784, 40.7128, -74.006);
    assert.ok(km > 400 && km < 600, String(km));
  });
});
