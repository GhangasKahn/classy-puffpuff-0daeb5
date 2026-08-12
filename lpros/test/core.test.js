import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  ebayFees,
  netProfitPerSale,
  listingsNeeded,
  expectedDailyProfit,
  stressForecast,
} from "../src/core/economics.js";
import { sellThroughProxy, updateGammaPoisson, WEAK_VELOCITY_PRIOR } from "../src/core/bayesian.js";
import { psychProxies } from "../src/core/psychology.js";
import { verifyProduct } from "../src/core/verify.js";
import { rankCandidates } from "../src/core/scoring.js";

describe("economics engine", () => {
  it("computes ~14% effective fees on $40 sale", () => {
    const f = ebayFees(40);
    assert.ok(f.fees > 5 && f.fees < 7);
    assert.ok(f.effectiveRate > 0.13 && f.effectiveRate < 0.16);
  });

  it("matches worked example leftover ballpark", () => {
    const r = netProfitPerSale({ salePrice: 40, productCost: 22, returnsBufferRate: 0 });
    // fees ~5.84, leftover ~12.16 before returns
    assert.ok(r.net > 11 && r.net < 13);
  });

  it("listings-needed for $120/day", () => {
    const n = listingsNeeded({ targetDailyProfit: 120, str: 0.018, avgNet: 9.4 });
    // 120 / (0.018 * 9.4) ≈ 709.22 → ceil 710
    assert.equal(n.listingsNeeded, 710);
    assert.ok(n.listingsExact > 709 && n.listingsExact < 710.3);
  });

  it("expected daily profit on 300 listings", () => {
    const e = expectedDailyProfit({ listings: 300, str: 0.018, avgNet: 9.4 });
    assert.ok(Math.abs(e.expectedDailyProfit - 50.76) < 0.02);
  });

  it("stress triad returns base/adverse/severe", () => {
    const s = stressForecast({
      listings: 300,
      str: 0.018,
      avgNet: 9.4,
      targetDailyProfit: 120,
    });
    assert.ok(s.base.expectedDailyProfit > s.adverse.expectedDailyProfit);
    assert.ok(s.adverse.expectedDailyProfit > s.severe.expectedDailyProfit);
  });
});

describe("bayesian helpers", () => {
  it("updates gamma-poisson mean upward with sales", () => {
    const post = updateGammaPoisson(WEAK_VELOCITY_PRIOR, 10, 10);
    assert.ok(post.mean > WEAK_VELOCITY_PRIOR.alpha / WEAK_VELOCITY_PRIOR.beta);
  });

  it("sell-through widens on small n", () => {
    const small = sellThroughProxy({ sold: 1, active: 1 });
    const big = sellThroughProxy({ sold: 50, active: 50 });
    assert.ok(big.confidence > small.confidence);
  });
});

describe("psychology proxies", () => {
  it("flags complexity + impulse remorse", () => {
    const p = psychProxies({
      title: "Funny viral LED DIY assembly kit novelty gadget",
      salePrice: 79,
      categoryMedianPrice: 30,
    });
    assert.ok(p.remorseRisk > 0.4);
  });

  it("prefers utility tools", () => {
    const p = psychProxies({
      title: "Stainless steel organizer mount tool holder",
      salePrice: 28,
      categoryMedianPrice: 30,
      velocityPerDay: 1.2,
      active: 20,
    });
    assert.ok(p.psychFit > 0.35);
  });
});

describe("zero-trust verify", () => {
  it("FAIL on retail arbitrage", () => {
    const r = verifyProduct({
      salePrice: 40,
      productCost: 20,
      leadTimeDays: 5,
      activeCount: 30,
      soldCount: 8,
      soldEvidenceMissing: false,
      evidenceStatus: "ok",
      demandConfidence: 0.5,
      density: 100,
      velocityPerDay: 1,
      remorseRisk: 0.2,
      retailArbitrage: true,
      demandSources: ["ebay_browse", "terapeak"],
      title: "x",
    });
    assert.equal(r.decision, "FAIL");
    assert.ok(r.criticalFail.includes("compliance"));
  });

  it("PASS healthy wholesale candidate", () => {
    const r = verifyProduct({
      salePrice: 40,
      productCost: 18,
      altProductCost: 19,
      leadTimeDays: 5,
      activeCount: 40,
      soldCount: 12,
      soldEvidenceMissing: false,
      evidenceStatus: "ok",
      demandConfidence: 0.5,
      density: 120,
      velocityPerDay: 0.8,
      remorseRisk: 0.25,
      retailArbitrage: false,
      sourcePath: "wholesale",
      demandSources: ["ebay_browse", "terapeak"],
      title: "replacement filter seal kit",
    });
    assert.equal(r.decision, "PASS");
  });

  it("rejects ZIK-only demand", () => {
    const r = verifyProduct({
      salePrice: 40,
      productCost: 18,
      leadTimeDays: 5,
      activeCount: 40,
      soldCount: 12,
      soldEvidenceMissing: false,
      evidenceStatus: "ok",
      demandConfidence: 0.5,
      density: 120,
      velocityPerDay: 0.8,
      remorseRisk: 0.25,
      demandSources: ["zik"],
      title: "x",
    });
    assert.equal(r.results.demandSignal.pass, false);
  });
});

describe("ranking", () => {
  it("ranks higher-margin lower-remorse first", () => {
    const { ranked, rejected } = rankCandidates([
      {
        ref: "bad",
        title: "viral meme novelty diy kit",
        salePrice: 55,
        productCost: 40,
        activeCount: 200,
        soldCount: 2,
        leadTimeDays: 5,
        demandSources: ["ebay_browse", "terapeak"],
        evidenceStatus: "partial",
      },
      {
        ref: "good",
        title: "pro tool organizer mount stainless",
        salePrice: 36,
        productCost: 14,
        altProductCost: 14.5,
        activeCount: 25,
        soldCount: 15,
        leadTimeDays: 5,
        soldEvidenceMissing: false,
        evidenceStatus: "ok",
        demandSources: ["ebay_browse", "terapeak"],
        sourcePath: "wholesale",
      },
    ]);
    assert.ok(ranked.length >= 1);
    assert.equal(ranked[0].ref, "good");
    assert.ok(rejected.length >= 0);
  });
});
