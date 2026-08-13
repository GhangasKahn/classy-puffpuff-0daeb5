import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  keywordMomentum,
  categoryTrendSnapshot,
  buildCampaignTrends,
} from "../src/core/trends.js";

describe("trends", () => {
  it("detects rising keywords vs baseline", () => {
    const baseline = Array(20).fill("desk organizer wood tray");
    const fresh = [
      ...Array(10).fill("walnut modular desk organizer upgrade"),
      ...Array(5).fill("desk organizer wood tray"),
    ];
    const m = keywordMomentum({ freshTitles: fresh, baselineTitles: baseline, minFresh: 2 });
    assert.ok(m.rising.some((r) => r.term === "walnut" || r.term === "modular"));
    assert.ok(m.caveat.includes("Proxy"));
  });

  it("builds campaign ideas across categories", () => {
    const trends = buildCampaignTrends({
      ideasTarget: 120,
      lanes: [
        {
          categoryId: "1",
          label: "Desk",
          titles: ["oak desk organizer", "bamboo clutter tray", "walnut cable organizer"],
          snapshot: categoryTrendSnapshot({
            categoryId: "1",
            label: "Desk",
            activeTotal: 5000,
            density: 20,
            priceLadder: { p10: 30, p50: 50, p75: 70, p90: 90 },
            newlyListedMedian: 55,
            bestMatchMedian: 50,
            avgImageCount: 6,
          }),
          momentum: keywordMomentum({
            freshTitles: ["walnut modular organizer", "walnut modular organizer"],
            baselineTitles: ["desk tray wood", "desk tray wood"],
            minFresh: 1,
          }),
        },
        {
          categoryId: "2",
          label: "Kitchen",
          titles: ["bamboo utensil organizer", "wood spice rack"],
          snapshot: categoryTrendSnapshot({
            categoryId: "2",
            label: "Kitchen",
            activeTotal: 2000,
            density: 10,
            priceLadder: { p10: 25, p50: 40, p75: 55, p90: 70 },
            avgImageCount: 4,
          }),
          momentum: { rising: [{ term: "bamboo", lift: 2, delta: 0.1 }] },
        },
      ],
    });
    assert.ok(trends.ideaCount >= 50);
    assert.equal(trends.hottestCategory.categoryId, "1");
    assert.ok(trends.materialDemand.some((m) => m.term === "oak" || m.term === "bamboo"));
  });
});
