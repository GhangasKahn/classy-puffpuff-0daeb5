import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { computeMarketMetrics } from "../src/core/market_metrics.js";
import { filterCandidate, applyFilters } from "../src/core/filters.js";
import { rankMarket, DEFAULT_WEIGHTS } from "../src/core/ranker.js";

describe("market metrics", () => {
  it("flags synthetic STR when sold missing", () => {
    const m = computeMarketMetrics({
      soldCount: 0,
      activeCount: 40,
      salePrice: 49,
      categoryMedianPrice: 45,
      title: "Solid oak desk organizer clutter upgrade",
      perceivedValue: 0.55,
    });
    assert.equal(m.sellThrough.source, "synthetic_or_active_only");
    assert.ok(m.ctr.caveat.includes("Not official"));
    assert.equal(m.purchaseHistory.available, false);
  });

  it("uses sold comps for purchase history", () => {
    const m = computeMarketMetrics({
      soldCount: 12,
      activeCount: 30,
      soldEvidenceMissing: false,
      soldComps: [{ price: 48, date: "2026-08-01", title: "oak organizer", kind: "sold" }],
      salePrice: 49,
      watchCount: 22,
    });
    assert.ok(m.sellThrough.rate > 0);
    assert.equal(m.purchaseHistory.available, true);
    assert.equal(m.purchaseHistory.count, 1);
    assert.ok(m.popularity > 0);
  });
});

describe("filters + ranker", () => {
  it("kills scam and keeps solid wood organizer", () => {
    const { kept, rejected } = applyFilters([
      {
        title: "6-600Pcs Hot Sale!!! FREE SHIPPING***",
        salePrice: 55,
        productCost: 20,
      },
      {
        title: "Solid oak desk organizer tray clutter upgrade heavy-duty",
        salePrice: 49,
        productCost: 18,
        soldEvidenceMissing: true,
      },
    ]);
    assert.ok(rejected.some((r) => /scam|qty/i.test(JSON.stringify(r.filter.hardFails))));
    assert.ok(kept.length >= 1);
    assert.equal(kept[0].filter.decision, "CONDITIONAL");
  });

  it("ranks higher cash + PV ahead", () => {
    const result = rankMarket(
      [
        {
          title: "Thin plastic desk clip novelty",
          salePrice: 36,
          productCost: 20,
          activeCount: 200,
          soldCount: 1,
          perceivedValue: 0.1,
        },
        {
          title: "Solid walnut under-desk cable tray organizer upgrade no-drill",
          salePrice: 54,
          productCost: 18,
          activeCount: 40,
          soldCount: 15,
          soldEvidenceMissing: false,
          watchCount: 40,
          perceivedValue: 0.6,
          image: "https://example.com/a.jpg",
          soldComps: [{ price: 52, date: "2026-07-01", kind: "sold", title: "walnut tray" }],
        },
      ],
      { minPrice: 35, maxPrice: 200, costRatio: 0.4 }
    );
    assert.equal(result.algorithm, "LPROS_Rank_v1");
    assert.ok(Object.keys(DEFAULT_WEIGHTS).length >= 5);
    assert.ok(result.ranked.length >= 1);
    assert.match(result.ranked[0].title, /walnut|oak|solid/i);
    assert.equal(result.ranked[0].rank, 1);
    assert.ok(result.ranked[0].metrics.ctr.rate >= 0);
    assert.ok(result.stats.withImages >= 1);
  });
});
