/**
 * Filter pipeline — hard kills then soft demotions.
 * Order is intentional: cheap/deterministic gates first.
 */

import { psychProxies } from "./psychology.js";
import { netProfitPerSale } from "./economics.js";

export const FILTER_STAGES = [
  "price_band",
  "scam_kill",
  "compliance",
  "margin_floor",
  "perceived_value",
  "evidence_soft",
];

/**
 * @param {object} candidate
 * @param {object} [policy]
 */
export function filterCandidate(candidate, policy = {}) {
  const p = {
    minPrice: policy.minPrice ?? 35,
    maxPrice: policy.maxPrice ?? 200,
    minMargin: policy.minMargin ?? 0.12,
    minPerceivedValue: policy.minPerceivedValue ?? 0.25,
    costRatio: policy.costRatio ?? 0.4,
    allowConditional: policy.allowConditional !== false,
    requireSold: policy.requireSold === true,
    ...policy,
  };

  const reasons = [];
  const soft = [];
  const price = Number(candidate.salePrice ?? candidate.price) || 0;
  const cost =
    candidate.productCost != null
      ? Number(candidate.productCost)
      : price > 0
        ? price * p.costRatio
        : 0;

  // 1. Price band
  if (price < p.minPrice || price > p.maxPrice) {
    reasons.push({ stage: "price_band", hard: true, detail: `$${price} outside $${p.minPrice}–$${p.maxPrice}` });
  }

  // 2. Scam kill
  const psych =
    candidate.psych ||
    psychProxies({
      title: candidate.title || "",
      salePrice: price,
      categoryMedianPrice: candidate.categoryMedianPrice || price,
    });
  if (psych.scammy || psych.killRecommendation) {
    reasons.push({
      stage: "scam_kill",
      hard: true,
      detail: (psych.scamHits || []).join(",") || "scammy",
    });
  }

  // 3. Compliance
  if (candidate.retailArbitrage) {
    reasons.push({ stage: "compliance", hard: true, detail: "retail_arbitrage" });
  }

  // 4. Margin floor
  const econ = netProfitPerSale({
    salePrice: price,
    productCost: cost,
    returnsBufferRate: candidate.returnsBufferRate ?? 0.04,
  });
  if (!(econ.net > 0 && econ.margin >= p.minMargin)) {
    reasons.push({
      stage: "margin_floor",
      hard: true,
      detail: `net $${econ.net} margin ${econ.marginPct}%`,
    });
  }

  // 5. Perceived value (hard if very low and no problem-solve)
  const pv = psych.perceivedValue ?? candidate.perceivedValue ?? 0;
  const problem = psych.features?.problemSolving || candidate.problemSolving;
  const upgrade = psych.features?.upgradeReplace || candidate.upgradeReplace;
  if (pv < p.minPerceivedValue && !problem && !upgrade) {
    reasons.push({
      stage: "perceived_value",
      hard: true,
      detail: `PV ${pv} < ${p.minPerceivedValue}`,
    });
  }

  // 6. Evidence soft
  const soldMissing = candidate.soldEvidenceMissing ?? !(candidate.soldCount > 0);
  if (soldMissing) {
    soft.push({
      stage: "evidence_soft",
      hard: false,
      detail: "sold_evidence_missing",
    });
    if (p.requireSold) {
      reasons.push({ stage: "evidence_soft", hard: true, detail: "requireSold policy" });
    }
  }
  if (candidate.altProductCost == null && candidate.productCost != null) {
    soft.push({ stage: "evidence_soft", hard: false, detail: "single_source_cost" });
  }

  const hardFails = reasons.filter((r) => r.hard);
  const pass = hardFails.length === 0;
  const decision = !pass ? "REJECT" : soft.length ? "CONDITIONAL" : "PASS";

  return {
    pass,
    decision: p.allowConditional || decision !== "CONDITIONAL" ? decision : decision === "REJECT" ? "REJECT" : "PASS",
    hardFails,
    softFlags: soft,
    psych,
    economics: econ,
    stages: FILTER_STAGES,
  };
}

/**
 * Apply filter to a list; returns kept + rejected with reasons.
 */
export function applyFilters(candidates, policy = {}) {
  const kept = [];
  const rejected = [];
  for (const c of candidates) {
    const f = filterCandidate(c, policy);
    const row = { ...c, filter: f, perceivedValue: f.psych?.perceivedValue ?? c.perceivedValue };
    if (f.pass) kept.push(row);
    else rejected.push(row);
  }
  return {
    kept,
    rejected,
    stats: {
      input: candidates.length,
      kept: kept.length,
      rejected: rejected.length,
      conditional: kept.filter((k) => k.filter.decision === "CONDITIONAL").length,
    },
  };
}
