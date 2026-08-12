/**
 * Fulfillment layer — AutoDS/DSers-class capabilities as open adapters.
 * We do NOT reimplement closed supplier scrapers; we define the control plane
 * that wraps official eBay Fulfillment API + optional paid automators.
 */

export const FULFILLMENT_PROVIDERS = {
  ebay_official: {
    name: "eBay Fulfillment API",
    cost: "free (developer)",
    strengths: ["order pull", "tracking push", "highest trust"],
    gaps: ["no supplier auto-order"],
  },
  dsers: {
    name: "DSers",
    cost: "free–$50/mo",
    strengths: ["AliExpress bulk order", "tracking sync", "low entry cost"],
    gaps: ["AliExpress-centric", "newer eBay integration"],
  },
  autods: {
    name: "AutoDS",
    cost: "~$27+/mo",
    strengths: ["multi-supplier", "stock/price monitor", "mature automation"],
    gaps: ["SaaS lock-in", "temptation to list junk at scale"],
  },
  easync: {
    name: "Easync",
    cost: "paid",
    strengths: ["eBay-native protection", "repricing"],
    gaps: ["higher cost"],
  },
};

/**
 * Zero-trust decision: auto-fulfill vs hold for human/agent review.
 */
export function fulfillDecision(order, policy = {}) {
  const maxAutoValue = policy.maxAutoValue ?? 80;
  const requireTrackingSlaHours = policy.requireTrackingSlaHours ?? 48;
  const flags = [];

  if (!order?.lineItems?.length) flags.push("empty_order");
  if (order.retailArbitrage) flags.push("retail_arbitrage_forbidden");
  if (order.supplierCost == null) flags.push("missing_supplier_cost");
  if (order.buyerTotal > maxAutoValue) flags.push("over_auto_value_limit");
  if (order.supplierLeadDays > (policy.maxLeadDays ?? 12)) flags.push("lead_time_risk");
  if (order.margin != null && order.margin < (policy.minMargin ?? 0.12)) flags.push("margin_below_floor");

  const auto =
    flags.length === 0 &&
    order.supplierConfirmed === true &&
    order.policyCompliant === true;

  return {
    action: auto ? "AUTO_FULFILL" : "HOLD_REVIEW",
    flags,
    requireTrackingSlaHours,
    checklist: [
      "Verify supplier stock + landed cost vs listing",
      "Place supplier order with correct ship-to",
      "Retrieve tracking within SLA",
      "Push tracking to eBay Fulfillment API",
      "Log outcome (on-time, cost variance, INR risk) for conditioning",
    ],
    vsAutods: {
      superior: [
        "explicit HOLD on weak margin / long lead / missing cost",
        "conditioning loop from fulfillment failures",
        "never auto-scale scammy SKUs",
      ],
      useAutodsAs: "optional executor under this control plane — not the brain",
    },
  };
}

export function providerMatrix() {
  return {
    recommendation:
      "Start: eBay Fulfillment API + manual/semi supplier. Add DSers if AliExpress-heavy. Wrap AutoDS later as untrusted executor.",
    providers: FULFILLMENT_PROVIDERS,
  };
}
