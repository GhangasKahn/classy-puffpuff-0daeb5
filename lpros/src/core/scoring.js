/**
 * Composite ranking: expected net under uncertainty × psychFit, after hard kills.
 * S ≈ uncertaintyShrink(E[net], conf) × psychFit × viability
 */

import { netProfitPerSale } from "./economics.js";
import { sellThroughProxy, competitionDensity, uncertaintyShrink, updateGammaPoisson, WEAK_VELOCITY_PRIOR } from "./bayesian.js";
import { psychProxies } from "./psychology.js";
import { verifyProduct } from "./verify.js";

export function scoreCandidate(raw, opts = {}) {
  const salePrice = Number(raw.salePrice ?? raw.suggestedValue ?? 0);
  const active = Number(raw.activeCount ?? raw.active ?? 0);
  const sold = Number(raw.soldCount ?? raw.sold ?? 0);
  const productCost =
    raw.productCost != null
      ? Number(raw.productCost)
      : salePrice > 0
        ? salePrice * (opts.defaultCostRatio ?? 0.45)
        : 0;

  const st = sellThroughProxy({ sold, active });
  // velocity proxy: treat sold over ~14 day window if not provided
  const windowDays = Number(raw.windowDays ?? 14);
  const velocity = raw.velocityPerDay != null ? Number(raw.velocityPerDay) : sold / windowDays;
  const velPost = updateGammaPoisson(WEAK_VELOCITY_PRIOR, sold, Math.max(windowDays, 1));
  const dens = competitionDensity({ active, velocityPerDay: velPost.mean });

  const econ = netProfitPerSale({
    salePrice,
    shippingCharged: raw.shippingCharged || 0,
    productCost,
    shippingCostExtra: raw.shippingCostExtra || 0,
    returnsBufferRate: raw.returnsBufferRate ?? 0.04,
    hasStore: raw.hasStore,
    toolAmortPerSale: raw.toolAmortPerSale || 0,
  });

  const psych = psychProxies({
    title: raw.title || raw.ref || "",
    description: raw.description || "",
    salePrice,
    categoryMedianPrice: raw.categoryMedianPrice || salePrice,
    velocityPerDay: velPost.mean,
    active,
  });

  const demandConfidence = Math.min(
    1,
    0.5 * st.confidence + 0.5 * Math.min(1, (sold + active) / 40)
  );

  const shrunkNet = uncertaintyShrink(econ.net, demandConfidence, opts.shrinkK ?? 1);
  // Prefer high perceived value in the composite, not just psychFit × net
  const valueBoost = 0.55 + 0.45 * (psych.perceivedValue || 0);
  const composite = Math.max(0, shrunkNet) * psych.psychFit * valueBoost;

  const candidate = {
    ...raw,
    salePrice,
    productCost,
    activeCount: active,
    soldCount: sold,
    velocityPerDay: velPost.mean,
    density: dens.density,
    demandConfidence,
    remorseRisk: psych.remorseRisk,
    perceivedValue: psych.perceivedValue,
    variationPotential: psych.variationPotential,
    scammy: psych.scammy,
    scamHits: psych.scamHits,
    problemSolving: Boolean(psych.features?.problemSolving),
    upgradeReplace: Boolean(psych.features?.upgradeReplace),
    soldEvidenceMissing: raw.soldEvidenceMissing ?? sold === 0,
    evidenceStatus: raw.evidenceStatus || (sold > 0 ? "ok" : active > 0 ? "partial" : "listings-needed"),
    demandSources: raw.demandSources || ["ebay_browse"],
    retailArbitrage: Boolean(raw.retailArbitrage),
    complianceViolations: raw.complianceViolations || [],
    sourcePath: raw.sourcePath || "wholesale_unspecified",
    leadTimeDays: raw.leadTimeDays ?? 7,
    altProductCost: raw.altProductCost,
  };

  const verification = verifyProduct(candidate, opts.thresholds);

  return {
    ref: raw.ref || raw.title || "candidate",
    title: raw.title || raw.ref || "",
    category: raw.category,
    url: raw.url,
    evidenceStatus: candidate.evidenceStatus,
    economics: econ,
    sellThrough: st,
    velocity: velPost,
    density: dens,
    psych,
    demandConfidence,
    shrunkNet: Math.round(shrunkNet * 100) / 100,
    composite: Math.round(composite * 1000) / 1000,
    verification,
    kill:
      verification.decision === "FAIL" ||
      psych.killRecommendation ||
      psych.scammy ||
      psych.remorseRisk > (opts.thresholds?.maxRemorse ?? 0.55) ||
      econ.net <= 0 ||
      salePrice < (opts.thresholds?.minSalePrice ?? 35) ||
      salePrice > (opts.thresholds?.maxSalePrice ?? 200),
  };
}

export function rankCandidates(list, opts = {}) {
  const scored = list.map((c) => scoreCandidate(c, opts));
  const survivors = scored.filter((s) => !s.kill && s.verification.decision !== "FAIL");
  survivors.sort((a, b) => b.composite - a.composite);
  return {
    ranked: survivors,
    rejected: scored.filter((s) => s.kill || s.verification.decision === "FAIL"),
    conditional: survivors.filter((s) => s.verification.decision === "CONDITIONAL"),
  };
}
