/**
 * Hermes-style sequential pipeline (lightweight orchestration — no heavy framework).
 * Data → Feature → Psychology → Margin/Gate → Rank
 * Cash-is-truth: Economics Engine inside Margin Gate is authoritative.
 */
import { loadEbayEnv } from "./agents/_env.js";
import { buildCandidatesFromQuery } from "./agents/data.js";
import { extractFeatures } from "./agents/feature.js";
import { scorePsychology } from "./agents/psychology.js";
import { runMarginGate, forecastListings } from "./agents/margin_gate.js";
import { rank } from "./agents/ranking.js";
import { logOutcome } from "./agents/outcome.js";

export async function runResearchPipeline({
  category = "Watch",
  queries = ["126610LN"],
  productCostRatio = 0.45,
  leadTimeDays = 7,
  sourcePath = "wholesale_unspecified",
  thresholds,
  targetDailyProfit = 50,
  assumedStr = 0.015,
  minPrice = 35,
  maxPrice = 200,
} = {}) {
  await loadEbayEnv();

  const band = {
    minSalePrice: thresholds?.minSalePrice ?? minPrice,
    maxSalePrice: thresholds?.maxSalePrice ?? maxPrice,
  };
  const gateThresholds = { ...thresholds, ...band };

  const raw = await buildCandidatesFromQuery({
    category,
    queries,
    productCostRatio,
    leadTimeDays,
    sourcePath,
    minPrice: band.minSalePrice,
    maxPrice: band.maxSalePrice,
  });

  const enriched = raw.map((c) => {
    const f = extractFeatures(c);
    const p = scorePsychology(f);
    return runMarginGate(p, gateThresholds);
  });

  // Re-score via composite ranker (includes verify again — consistent)
  const ranked = rank(
    enriched.map((e) => ({
      ...e,
      density: e.features?.density?.density,
      velocityPerDay: e.features?.velocity?.mean,
      demandConfidence: e.features?.sellThrough?.confidence,
      remorseRisk: e.psych?.remorseRisk,
    })),
    { thresholds: gateThresholds, defaultCostRatio: productCostRatio }
  );

  const top = ranked.ranked[0];
  const avgNet = top?.economics?.net || 0;
  const forecast = forecastListings({
    targetDailyProfit,
    str: assumedStr,
    avgNet: Math.max(avgNet, 0.01),
    listings: 300,
  });

  const report = {
    generatedAt: new Date().toISOString(),
    category,
    queries,
    priceBand: { min: band.minSalePrice, max: band.maxSalePrice },
    counts: {
      candidates: raw.length,
      ranked: ranked.ranked.length,
      rejected: ranked.rejected.length,
      conditional: ranked.conditional.length,
    },
    top: ranked.ranked.slice(0, 10).map(summarize),
    rejectedSample: ranked.rejected.slice(0, 5).map(summarize),
    forecast,
    notes: [
      `High-ticket band: $${band.minSalePrice}–$${band.maxSalePrice} (sub-minimum filtered).`,
      "PsychFit is provisional proxy scoring — not validated probability.",
      "Marketplace Insights sold data may be unavailable (soldEvidenceMissing).",
      "Retail arbitrage is compliance FAIL — wholesale/manufacturer only.",
    ],
  };

  logOutcome({
    type: "pipeline_run",
    category,
    queries,
    priceBand: report.priceBand,
    ranked: report.counts.ranked,
    rejected: report.counts.rejected,
  });

  return report;
}

function summarize(s) {
  return {
    ref: s.ref,
    title: (s.title || "").slice(0, 80),
    salePrice: s.economics?.salePrice ?? s.salePrice,
    net: s.economics?.net,
    marginPct: s.economics?.marginPct,
    composite: s.composite,
    decision: s.verification?.decision,
    evidenceStatus: s.evidenceStatus,
    psychFit: s.psych?.psychFit,
    remorseRisk: s.psych?.remorseRisk ?? s.remorseRisk,
    confidence: s.verification?.verificationConfidence,
    url: s.url,
    flags: s.verification?.flags,
  };
}
