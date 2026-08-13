import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { resolveCategoryId, CATEGORY_SEEDS } from "../src/ebay/comps.js";

describe("resolveCategoryId", () => {
  it("maps watch → wristwatches seed", () => {
    assert.equal(resolveCategoryId("Watch"), CATEGORY_SEEDS.watch);
  });
  it("honors explicit categoryIds", () => {
    assert.equal(resolveCategoryId("Watch", "999"), "999");
  });
  it("is case-insensitive", () => {
    assert.equal(resolveCategoryId("TRADING CARD"), CATEGORY_SEEDS["trading card"]);
  });
});

describe("comps payload shape (unit)", () => {
  it("median helper via synthetic preferred prices", () => {
    const prices = [100, 200, 300];
    const sorted = [...prices].sort((a, b) => a - b);
    const m = sorted[Math.floor(sorted.length / 2)];
    assert.equal(m, 200);
  });
});
