import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { fulfillDecision, providerMatrix } from "../src/fulfill/adapter.js";

describe("fulfillment control plane", () => {
  it("HOLDs when supplier cost missing", () => {
    const d = fulfillDecision({
      buyerTotal: 40,
      supplierCost: null,
      supplierLeadDays: 5,
      margin: 0.2,
      supplierConfirmed: true,
      policyCompliant: true,
      lineItems: [{ sku: "x" }],
    });
    assert.equal(d.action, "HOLD_REVIEW");
    assert.ok(d.flags.includes("missing_supplier_cost"));
  });

  it("AUTO when clean", () => {
    const d = fulfillDecision({
      buyerTotal: 40,
      supplierCost: 15,
      supplierLeadDays: 5,
      margin: 0.25,
      supplierConfirmed: true,
      policyCompliant: true,
      lineItems: [{ sku: "x" }],
    });
    assert.equal(d.action, "AUTO_FULFILL");
  });

  it("exposes provider matrix", () => {
    const m = providerMatrix();
    assert.ok(m.providers.autods);
    assert.ok(m.providers.dsers);
    assert.ok(m.providers.ebay_official);
  });
});
