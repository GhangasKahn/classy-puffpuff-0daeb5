import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { hardenCandidate } from "../../lpros/src/core/evidence.js";
import { draftListing } from "../../lpros/src/agents/listing.js";
import { fulfillDecision } from "../src/fulfill/adapter.js";

describe("command evidence + listing wiring", () => {
  it("hardens a board-shaped candidate to PASS", () => {
    const r = hardenCandidate(
      {
        title: "Bamboo under-desk cable tray organizer upgrade",
        salePrice: 42,
        productCost: 16.8,
        productCostEstimated: true,
        leadTimeDays: 8,
        soldEvidenceMissing: true,
        evidenceStatus: "partial",
        demandSources: ["ebay_browse"],
        activeCount: 55,
        density: 60,
        perceivedValue: 0.5,
        problemSolving: true,
        remorseRisk: 0.28,
        scammy: false,
        hasImages: true,
        hasItemSpecifics: true,
        str: 0.015,
      },
      { soldCount: 18, productCost: 15, altProductCost: 15.5, demandSource: "terapeak" }
    );
    assert.equal(r.decision, "PASS");
    assert.ok(r.economics.net > 0);
  });

  it("drafts listing without LLM", () => {
    const d = draftListing({ title: "Oak wood desk mail sorter 6 slot", salePrice: 48 });
    assert.match(d.title, /Oak|Wood|desk/i);
    assert.ok(d.descriptionHtml.includes("<ul>"));
  });

  it("fulfill still HOLDs without supplier cost", () => {
    const d = fulfillDecision({
      buyerTotal: 60,
      lineItems: [{ sku: "x" }],
      supplierConfirmed: true,
      policyCompliant: true,
    });
    assert.equal(d.action, "HOLD_REVIEW");
  });
});
