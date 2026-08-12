/**
 * LPROS Rank — multi-factor ranking algorithm.
 *
 * Score is a weighted sum of normalized components with explicit penalties.
 * Weights are tunable; defaults favor cash + evidence over vanity popularity.
 */

import { computeMarketMetrics } from "./market_metrics.js";
import { filterCandidate } from "./filters.js";
import { uncertaintyShrink } from "./bayesian.js";

export const DEFAULT_WEIGHTS = {
  cash: 0.32, // shrunk net
  sellThrough: 0.18,
  popularity: 0.12,
  perceivedValue: 0.16,
  competition: 0.1, // inverse density
  ctrProxy: 0.08,
  evidence: 0.04, // bonus when sold evidence present
};

/**
 * Rank candidates after filter.
 * @param {object[]} candidates
 * @param {object} [opts]
 */
export function rankMarket(candidates, opts = {}) {
  const weights = { ...DEFAULT_WEIGHTS, ...(opts.weights || {}) };
  const policy = opts.filterPolicy || {
    minPrice: opts.minPrice ?? 35,
    maxPrice: opts.maxPrice ?? 200,
    costRatio: opts.costRatio ?? 0.4,
  };

  const filtered = [];
  const rejected = [];
  for (const c of candidates) {
    const f = filterCandidate(c, policy);
    if (!f.pass) {
      rejected.push({ ...c, filter: f, rankScore: 0 });
      continue;
    }
    filtered.push({ ...c, filter: f, economics: f.economics, psych: f.psych });
  }

  // First pass metrics for normalization
  const enriched = filtered.map((c, idx) => {
    const metrics = computeMarketMetrics({
      soldCount: c.soldCount,
      activeCount: c.activeCount,
      windowDays: c.windowDays ?? 90,
      soldEvidenceMissing: c.soldEvidenceMissing,
      soldComps: c.soldComps || c.purchaseHistory?.events,
      watchCount: c.watchCount,
      salePrice: c.salePrice ?? c.price,
      categoryMedianPrice: c.categoryMedianPrice,
      perceivedValue: c.psych?.perceivedValue ?? c.perceivedValue,
      sampleSize: filtered.length,
      sampleIndex: idx,
      title: c.title,
    });
    const net = c.economics?.net ?? 0;
    const conf = metrics.sellThrough.confidence;
    const shrunkNet = uncertaintyShrink(net, Math.max(conf, 0.15), opts.shrinkK ?? 1);
    return { ...c, metrics, shrunkNet };
  });

  const nets = enriched.map((e) => e.shrunkNet);
  const dens = enriched.map((e) => e.metrics.marketRank.density || 0);
  const maxNet = Math.max(...nets, 0.01);
  const maxDens = Math.max(...dens, 1);

  const scored = enriched.map((e) => {
    const components = {
      cash: clamp(e.shrunkNet / maxNet, 0, 1),
      sellThrough: clamp(e.metrics.sellThrough.rate, 0, 1) * e.metrics.sellThrough.confidence,
      popularity: e.metrics.popularity,
      perceivedValue: e.psych?.perceivedValue ?? e.perceivedValue ?? 0,
      competition: 1 - clamp(e.metrics.marketRank.density / maxDens, 0, 1),
      ctrProxy: clamp((e.metrics.ctr.rate || 0) / 0.12, 0, 1),
      evidence: e.soldEvidenceMissing === false || (e.soldCount || 0) > 0 ? 1 : 0,
    };

    let score = 0;
    for (const [k, w] of Object.entries(weights)) {
      score += w * (components[k] || 0);
    }

    // Penalties
    const flags = (e.filter?.softFlags || []).map((s) => s.detail);
    if (flags.includes("sold_evidence_missing")) score *= 0.85;
    if (flags.includes("single_source_cost")) score *= 0.92;
    if (e.psych?.scammy) score = 0;

    return {
      ...e,
      components,
      rankScore: Math.round(score * 10000) / 10000,
      image: e.image || e.imageUrl || (e.images && e.images[0]) || null,
      images: e.images || (e.image ? [e.image] : []),
    };
  });

  scored.sort((a, b) => b.rankScore - a.rankScore);
  const ranked = scored.map((row, i) => ({
    ...row,
    rank: i + 1,
    metrics: {
      ...row.metrics,
      marketRank: {
        ...row.metrics.marketRank,
        lprosRank: i + 1,
        percentile: scored.length ? round4(1 - i / scored.length) : null,
      },
    },
  }));

  return {
    algorithm: "LPROS_Rank_v1",
    weights,
    ranked,
    rejected,
    stats: {
      input: candidates.length,
      ranked: ranked.length,
      rejected: rejected.length,
      withImages: ranked.filter((r) => r.image).length,
      withPurchaseHistory: ranked.filter((r) => r.metrics.purchaseHistory.available).length,
    },
  };
}

function clamp(x, lo, hi) {
  return Math.min(hi, Math.max(lo, Number(x) || 0));
}
function round4(x) {
  return Math.round(Number(x) * 10000) / 10000;
}
