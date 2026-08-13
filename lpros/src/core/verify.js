/**
 * Zero-Trust Multi-Factor Verification Protocol (fail-closed).
 * Critical factors must pass; ≥6/8 overall; evidence log required.
 */

import { netProfitPerSale, stressForecast } from "./economics.js";

export const FACTORS = [
  "supplyReality",
  "demandSignal",
  "competitionDensity",
  "economicViability",
  "compliance",
  "remorseRisk",
  "listingFeasibility",
  "forecastSensitivity",
];

export const CRITICAL = new Set(["supplyReality", "economicViability", "compliance"]);

/**
 * @param {object} candidate - product candidate with costs, comps, flags
 * @param {object} [thresholds]
 */
export function verifyProduct(candidate, thresholds = {}) {
  const t = {
    minMargin: thresholds.minMargin ?? 0.12,
    minSalePrice: thresholds.minSalePrice ?? 35,
    maxSalePrice: thresholds.maxSalePrice ?? 200,
    maxDensity: thresholds.maxDensity ?? 800,
    maxRemorse: thresholds.maxRemorse ?? 0.55,
    minPerceivedValue: thresholds.minPerceivedValue ?? 0.25,
    minDemandConfidence: thresholds.minDemandConfidence ?? 0.15,
    maxCostVariancePct: thresholds.maxCostVariancePct ?? 0.15,
    minFactorsPass: thresholds.minFactorsPass ?? 6,
    ...thresholds,
  };

  const evidence = [];
  const results = {};

  // 1. Supply Reality
  const cost = Number(candidate.productCost);
  const altCost = candidate.altProductCost != null ? Number(candidate.altProductCost) : null;
  const leadDays = Number(candidate.leadTimeDays ?? 99);
  let supplyPass = Number.isFinite(cost) && cost > 0 && leadDays <= (candidate.maxLeadDays ?? 12);
  let supplyNote = supplyPass ? "cost + lead time present" : "missing cost or lead time too long";
  if (supplyPass && candidate.productCostEstimated && Number(candidate.salePrice) > 150) {
    supplyPass = false;
    supplyNote =
      "estimated cost on >$150 item rejected — require real supplier quote (zero-knowledge)";
  }
  if (supplyPass && altCost != null && altCost > 0) {
    const varPct = Math.abs(cost - altCost) / Math.max(cost, altCost);
    if (varPct > t.maxCostVariancePct) {
      supplyPass = false;
      supplyNote = `cost variance ${(varPct * 100).toFixed(1)}% exceeds tolerance`;
    } else {
      supplyNote += `; cross-check variance ${(varPct * 100).toFixed(1)}%`;
    }
  } else if (supplyPass && altCost == null) {
    supplyNote += "; SINGLE-SOURCE cost — zero-knowledge flag";
    // still pass but flagged
  }
  results.supplyReality = factor(supplyPass, supplyNote, {
    productCost: cost,
    altProductCost: altCost,
    leadTimeDays: leadDays,
    singleSource: altCost == null,
  });
  evidence.push(results.supplyReality);

  // 2. Demand Signal
  const soldEvidence = candidate.soldEvidenceMissing === false || (candidate.soldCount ?? 0) > 0;
  const demandConf = Number(candidate.demandConfidence ?? 0);
  const zikOnly = candidate.demandSources?.length === 1 && candidate.demandSources[0] === "zik";
  let demandPass =
    demandConf >= t.minDemandConfidence &&
    (soldEvidence || (candidate.activeCount ?? 0) >= 5) &&
    !zikOnly;
  let demandNote = soldEvidence
    ? "sold evidence present"
    : "active-only / soldEvidenceMissing — partial";
  if (zikOnly) {
    demandPass = false;
    demandNote = "ZIK-only demand rejected (zero-trust cross-check required)";
  }
  if ((candidate.evidenceStatus === "listings-needed")) {
    demandPass = false;
    demandNote = "listings-needed";
  }
  results.demandSignal = factor(demandPass, demandNote, {
    evidenceStatus: candidate.evidenceStatus,
    soldCount: candidate.soldCount,
    activeCount: candidate.activeCount,
    demandConfidence: demandConf,
    sources: candidate.demandSources || [],
  });
  evidence.push(results.demandSignal);

  // 3. Competition Density
  const density = Number(candidate.density ?? Infinity);
  const densityPass = density <= t.maxDensity;
  results.competitionDensity = factor(
    densityPass,
    densityPass ? `density ${density.toFixed(1)} ok` : `density ${density.toFixed(1)} > max ${t.maxDensity}`,
    { density, active: candidate.activeCount, velocity: candidate.velocityPerDay }
  );
  evidence.push(results.competitionDensity);

  // 4. Economic Viability (+ high-ticket price band)
  const sale = Number(candidate.salePrice) || 0;
  const inBand = sale >= t.minSalePrice && sale <= t.maxSalePrice;
  const econ = netProfitPerSale({
    salePrice: candidate.salePrice,
    shippingCharged: candidate.shippingCharged || 0,
    productCost: candidate.productCost,
    shippingCostExtra: candidate.shippingCostExtra || 0,
    returnsBufferRate: candidate.returnsBufferRate ?? 0.04,
    hasStore: candidate.hasStore,
    toolAmortPerSale: candidate.toolAmortPerSale || 0,
  });
  const econPass = inBand && econ.net > 0 && econ.margin >= t.minMargin;
  let econNote;
  if (!inBand) {
    econNote = `sale $${sale} outside high-ticket band $${t.minSalePrice}–$${t.maxSalePrice}`;
  } else if (!(econ.net > 0 && econ.margin >= t.minMargin)) {
    econNote = `net $${econ.net} margin ${econ.marginPct}% below floor ${t.minMargin * 100}%`;
  } else {
    econNote = `net $${econ.net} margin ${econ.marginPct}% · band ok`;
  }
  results.economicViability = factor(econPass, econNote, {
    ...econ,
    minSalePrice: t.minSalePrice,
    maxSalePrice: t.maxSalePrice,
    inBand,
  });
  evidence.push(results.economicViability);

  // 5. Compliance (+ scammy listing / policy red flags)
  const violations = [...(candidate.complianceViolations || [])];
  const retailArbitrage = Boolean(candidate.retailArbitrage);
  const scammy = Boolean(candidate.scammy);
  if (scammy) violations.push("scammy_listing_signals");
  if (retailArbitrage) violations.push("retail_arbitrage");
  const compliancePass = violations.length === 0;
  results.compliance = factor(
    compliancePass,
    compliancePass
      ? "no critical policy / scam flags"
      : `violations: ${violations.join(", ")}`,
    {
      violations,
      retailArbitrage,
      scammy,
      scamHits: candidate.scamHits || [],
      sourcePath: candidate.sourcePath || "unspecified",
    }
  );
  evidence.push(results.compliance);

  // 6. Remorse + perceived-value quality gate
  const remorse = Number(candidate.remorseRisk ?? 0.5);
  const perceived = Number(candidate.perceivedValue ?? 0);
  const variation = Number(candidate.variationPotential ?? 0);
  const qualityPass =
    remorse <= t.maxRemorse &&
    !scammy &&
    (perceived >= t.minPerceivedValue ||
      Boolean(candidate.problemSolving) ||
      Boolean(candidate.upgradeReplace));
  let qualityNote;
  if (scammy) qualityNote = `scam/red-flag kill (${(candidate.scamHits || []).join(", ")})`;
  else if (remorse > t.maxRemorse) qualityNote = `remorse ${remorse} > ${t.maxRemorse}`;
  else if (!(perceived >= t.minPerceivedValue || candidate.problemSolving || candidate.upgradeReplace)) {
    qualityNote = `weak perceived value ${perceived} (need problem-solve / upgrade / materials)`;
  } else {
    qualityNote = `remorse ${remorse} · perceivedValue ${perceived} · variation ${variation}`;
  }
  results.remorseRisk = factor(qualityPass, qualityNote, {
    remorseRisk: remorse,
    perceivedValue: perceived,
    variationPotential: variation,
    minPerceivedValue: t.minPerceivedValue,
    problemSolving: Boolean(candidate.problemSolving),
    upgradeReplace: Boolean(candidate.upgradeReplace),
  });
  evidence.push(results.remorseRisk);

  // 7. Listing Feasibility
  const hasImages = candidate.hasImages !== false;
  const hasSpecifics = candidate.hasItemSpecifics !== false;
  const listingPass = hasImages && hasSpecifics && Boolean(candidate.title || candidate.ref);
  results.listingFeasibility = factor(
    listingPass,
    listingPass ? "title/images/specifics feasible" : "missing listing essentials",
    { hasImages, hasItemSpecifics: hasSpecifics }
  );
  evidence.push(results.listingFeasibility);

  // 8. Forecast Sensitivity
  const str = Number(candidate.str ?? 0.01);
  const stress = stressForecast({
    listings: 100,
    str,
    avgNet: Math.max(econ.net, 0.01),
    targetDailyProfit: 50,
  });
  const stressedNet = econ.net * 0.85 * 0.8; // rough STR-20% + returns hit on contribution
  const stressPass = stressedNet > 0 && econ.margin * 0.7 >= t.minMargin * 0.75;
  results.forecastSensitivity = factor(
    stressPass,
    stressPass ? "survives Adverse stress" : "fails Adverse stress",
    { stress, stressedNetProxy: Math.round(stressedNet * 100) / 100 }
  );
  evidence.push(results.forecastSensitivity);

  const passCount = FACTORS.filter((k) => results[k].pass).length;
  const criticalFail = [...CRITICAL].filter((k) => !results[k].pass);
  const flags = [];
  if (results.supplyReality.detail?.singleSource) flags.push("single_source_cost");
  if (candidate.soldEvidenceMissing) flags.push("sold_evidence_missing");
  if (candidate.evidenceStatus === "partial") flags.push("partial_evidence");
  if (scammy) flags.push("scammy_listing");
  if (perceived < t.minPerceivedValue) flags.push("low_perceived_value");

  let decision = "FAIL";
  if (criticalFail.length === 0 && passCount >= t.minFactorsPass) {
    decision = flags.length ? "CONDITIONAL" : "PASS";
  } else if (criticalFail.length === 0 && passCount >= t.minFactorsPass - 1 && flags.length) {
    decision = "CONDITIONAL";
  }

  const confidence =
    passCount / FACTORS.length *
    (1 - 0.15 * flags.length) *
    (criticalFail.length ? 0.3 : 1);

  return {
    decision,
    passCount,
    factorCount: FACTORS.length,
    criticalFail,
    flags,
    verificationConfidence: Math.round(Math.max(0, confidence) * 1000) / 1000,
    results,
    evidence,
    economics: econ,
    thresholds: t,
  };
}

function factor(pass, note, detail) {
  return { pass: Boolean(pass), note, detail };
}
