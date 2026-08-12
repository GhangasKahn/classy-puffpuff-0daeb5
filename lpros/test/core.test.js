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
import { hardenCandidate } from "../src/core/evidence.js";
import { rankCandidates } from "../src/core/scoring.js";
import { draftListing } from "../src/agents/listing.js";

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
    assert.ok(p.remorseRisk > 0.4 || p.scammy);
  });

  it("prefers utility tools", () => {
    const p = psychProxies({
      title: "Stainless steel organizer mount tool holder desk clutter",
      salePrice: 38,
      categoryMedianPrice: 40,
      velocityPerDay: 1.2,
      active: 20,
    });
    assert.ok(p.psychFit > 0.3);
    assert.ok(p.perceivedValue > 0.2);
  });

  it("kills scammy mega-lot dropship spam", () => {
    const p = psychProxies({
      title: "6-600Pcs Magnetic Cable Clips!! Hot Sale Bulk Lot FREE SHIPPING***",
      salePrice: 105,
      categoryMedianPrice: 40,
    });
    assert.equal(p.scammy, true);
    assert.ok(p.killRecommendation);
    assert.ok(p.scamHits.includes("qty_spam") || p.scamHits.includes("title_spam"));
  });

  it("scores upgrade + materials + problem-solve high", () => {
    const p = psychProxies({
      title:
        "Solid walnut under-desk cable tray — heavy-duty upgrade replaces plastic clips, no-drill clutter solution",
      salePrice: 49,
      categoryMedianPrice: 45,
      velocityPerDay: 0.8,
      active: 30,
    });
    assert.ok(p.perceivedValue >= 0.4);
    assert.ok(p.features.problemSolving === 1);
    assert.ok(p.features.upgradeReplace === 1);
    assert.equal(p.scammy, false);
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
      perceivedValue: 0.5,
      problemSolving: true,
      upgradeReplace: true,
      retailArbitrage: false,
      sourcePath: "wholesale",
      demandSources: ["ebay_browse", "terapeak"],
      title: "solid stainless desk organizer tray clutter upgrade",
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

  it("FAIL sale below high-ticket floor $35", () => {
    const r = verifyProduct({
      salePrice: 18,
      productCost: 7,
      leadTimeDays: 5,
      activeCount: 40,
      soldCount: 12,
      soldEvidenceMissing: false,
      evidenceStatus: "ok",
      demandConfidence: 0.5,
      density: 120,
      velocityPerDay: 0.8,
      remorseRisk: 0.25,
      demandSources: ["ebay_browse", "terapeak"],
      title: "cheap clip",
    });
    assert.equal(r.decision, "FAIL");
    assert.equal(r.results.economicViability.pass, false);
    assert.match(r.results.economicViability.note, /outside high-ticket band/);
  });
});

describe("evidence harden", () => {
  it("turns CONDITIONAL into PASS with Terapeak + dual cost", () => {
    const weak = {
      title: "Solid oak desk organizer clutter tray upgrade",
      salePrice: 49,
      productCost: 49 * 0.4,
      productCostEstimated: true,
      leadTimeDays: 7,
      soldEvidenceMissing: true,
      evidenceStatus: "partial",
      demandSources: ["ebay_browse"],
      activeCount: 40,
      density: 40,
      perceivedValue: 0.55,
      problemSolving: true,
      remorseRisk: 0.3,
      scammy: false,
      hasImages: true,
      hasItemSpecifics: true,
      str: 0.02,
    };
    const before = hardenCandidate(weak, {});
    assert.ok(before.decision === "CONDITIONAL" || before.remainingFlags.includes("sold_evidence_missing"));

    const after = hardenCandidate(weak, {
      soldCount: 24,
      productCost: 18,
      altProductCost: 19,
      leadTimeDays: 6,
      demandSource: "terapeak",
    });
    assert.equal(after.decision, "PASS");
    assert.equal(after.cleared, true);
    assert.ok(!after.remainingFlags.includes("sold_evidence_missing"));
    assert.ok(!after.remainingFlags.includes("single_source_cost"));
  });
});

describe("listing draft", () => {
  it("builds title and bullets from material cues", () => {
    const d = draftListing({
      title: "Desk Organizer 5 Tray Letter Sorter Brown",
      salePrice: 54,
    });
    assert.ok(d.title.length > 10);
    assert.ok(d.bullets.length >= 4);
    assert.ok(d.itemSpecifics.Type);
    assert.equal(d.scammy, false);
  });
});

describe("ranking", () => {
  it("ranks higher-margin lower-remorse first", () => {
    const { ranked, rejected } = rankCandidates([
      {
        ref: "bad",
        title: "6-600Pcs viral meme novelty diy kit Hot Sale!!! FREE SHIPPING***",
        salePrice: 55,
        productCost: 20,
        activeCount: 200,
        soldCount: 2,
        leadTimeDays: 5,
        demandSources: ["ebay_browse", "terapeak"],
        evidenceStatus: "partial",
      },
      {
        ref: "good",
        title:
          "Solid stainless steel desk organizer tray — heavy-duty upgrade replaces plastic clutter mount",
        salePrice: 42,
        productCost: 16,
        altProductCost: 16.5,
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
    assert.ok(rejected.some((r) => r.ref === "bad" || r.psych?.scammy));
  });
});
