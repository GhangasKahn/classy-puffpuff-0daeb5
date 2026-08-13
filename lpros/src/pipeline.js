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
import { rankMarket } from "./core/ranker.js";

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
  categoryId,
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
    categoryIds: categoryId,
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

  // Market ranker (images + STR/CTR proxies + LPROS_Rank)
  const market = rankMarket(
    enriched.map((e) => ({
      ...e,
      salePrice: e.salePrice,
      soldCount: e.soldCount,
      activeCount: e.activeCount,
      soldEvidenceMissing: e.soldEvidenceMissing,
      soldComps: e.soldComps || e.purchaseHistory,
      watchCount: e.watchCount,
      categoryMedianPrice: e.categoryMedianPrice,
      perceivedValue: e.psych?.perceivedValue,
      image: e.image,
      images: e.images,
      title: e.title,
      url: e.url,
      productCost: e.productCost,
    })),
    {
      minPrice: band.minSalePrice,
      maxPrice: band.maxSalePrice,
      costRatio: productCostRatio,
    }
  );

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
    // Ranker rejection must never hide live Browse listings from the desk.
    liveItems: raw
      .filter((c) => c.url && !c.synthetic)
      .map((c) => ({
        id: c.id || c.itemId || null,
        itemId: c.itemId || c.id || null,
        title: c.title,
        price: c.salePrice,
        salePrice: c.salePrice,
        url: c.url,
        image: c.image,
        images: c.images || [],
        thumbnail: c.thumbnail || c.image || null,
        watchCount: c.watchCount ?? null,
        listingDate: c.listingDate || null,
        seller: c.seller || null,
        source: "ebay_browse",
      })),
    market: {
      algorithm: market.algorithm,
      weights: market.weights,
      stats: market.stats,
      board: market.ranked.slice(0, 15).map(summarizeMarket),
      viz: buildVizPayload(market.ranked.slice(0, 20)),
    },
    forecast,
    notes: [
      `High-ticket band: $${band.minSalePrice}–$${band.maxSalePrice} (sub-minimum filtered).`,
      "Kill scammy dropship tells (qty spam, lots, clickbait, replicas). Prefer problem-solve / upgrade / materials.",
      "PsychFit is provisional proxy scoring — not validated probability.",
      "CTR is an engagement PROXY — not official eBay CTR.",
      "Purchase history requires Marketplace Insights entitlement or Terapeak evidence pack.",
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
    perceivedValue: s.psych?.perceivedValue ?? s.perceivedValue,
    variationPotential: s.psych?.variationPotential ?? s.variationPotential,
    remorseRisk: s.psych?.remorseRisk ?? s.remorseRisk,
    scammy: s.psych?.scammy ?? s.scammy,
    scamHits: s.psych?.scamHits ?? s.scamHits,
    confidence: s.verification?.verificationConfidence,
    url: s.url,
    image: s.image || s.thumbnail || null,
    images: s.images || [],
    watchCount: s.watchCount ?? null,
    flags: s.verification?.flags,
    psychNotes: s.psych?.notes,
  };
}

function summarizeMarket(row) {
  return {
    rank: row.rank,
    rankScore: row.rankScore,
    title: (row.title || "").slice(0, 100),
    salePrice: row.salePrice ?? row.price,
    net: row.economics?.net ?? row.shrunkNet,
    image: row.image,
    images: (row.images || []).slice(0, 4),
    url: row.url,
    decision: row.filter?.decision,
    sellThrough: row.metrics?.sellThrough?.rate,
    sellThroughCi: row.metrics?.sellThrough?.ci90,
    strConfidence: row.metrics?.sellThrough?.confidence,
    strSource: row.metrics?.sellThrough?.source,
    ctrProxy: row.metrics?.ctr?.rate,
    ctrCaveat: row.metrics?.ctr?.caveat,
    popularity: row.metrics?.popularity,
    watches: row.metrics?.watches,
    purchaseHistoryCount: row.metrics?.purchaseHistory?.count || 0,
    purchaseHistory: row.metrics?.purchaseHistory,
    components: row.components,
    softFlags: (row.filter?.softFlags || []).map((f) => f.detail),
  };
}

/** Compact series for desk charts (SVG). */
function buildVizPayload(ranked) {
  return {
    priceVsRank: ranked.map((r) => ({
      rank: r.rank,
      price: r.salePrice ?? r.price,
      score: r.rankScore,
      title: (r.title || "").slice(0, 40),
    })),
    strBars: ranked.map((r) => ({
      rank: r.rank,
      str: r.metrics?.sellThrough?.rate || 0,
      conf: r.metrics?.sellThrough?.confidence || 0,
    })),
    popularityBars: ranked.map((r) => ({
      rank: r.rank,
      popularity: r.metrics?.popularity || 0,
      ctrProxy: r.metrics?.ctr?.rate || 0,
    })),
    gallery: ranked.slice(0, 12).map((r) => ({
      rank: r.rank,
      title: (r.title || "").slice(0, 70),
      image: r.image,
      price: r.salePrice ?? r.price,
      url: r.url,
      score: r.rankScore,
    })),
  };
}
