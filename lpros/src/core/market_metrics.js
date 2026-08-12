/**
 * Market metrics — STR, popularity, rank, CTR proxies, purchase-history shape.
 *
 * Honesty contract:
 * - Official eBay CTR / full purchase history are NOT in Browse app tokens.
 * - STR uses sold/(sold+active) when sold exists; else synthetic prior (flagged).
 * - CTR is an engagement PROXY from watches/price/title — never label as official CTR.
 * - Purchase history = Insights sold comps when entitled; else empty + listings-needed.
 */

import { sellThroughProxy, updateGammaPoisson, WEAK_VELOCITY_PRIOR, competitionDensity } from "./bayesian.js";

/**
 * @param {object} input
 * @param {number} [input.soldCount]
 * @param {number} [input.activeCount]
 * @param {number} [input.windowDays]
 * @param {boolean} [input.soldEvidenceMissing]
 * @param {Array} [input.soldComps] - purchase/sold events
 * @param {number} [input.watchCount]
 * @param {number} [input.salePrice]
 * @param {number} [input.categoryMedianPrice]
 * @param {number} [input.perceivedValue]
 * @param {number} [input.sampleSize] - browse sample size for relative rank
 * @param {number} [input.sampleIndex] - 0-based position in sorted sample (optional)
 * @param {string} [input.title]
 */
export function computeMarketMetrics(input = {}) {
  const sold = Math.max(0, Number(input.soldCount) || 0);
  const active = Math.max(0, Number(input.activeCount) || 0);
  const windowDays = Math.max(1, Number(input.windowDays) || 90);
  const soldMissing = input.soldEvidenceMissing ?? sold === 0;
  const watches = input.watchCount != null ? Number(input.watchCount) : null;
  const price = Number(input.salePrice) || 0;
  const median = Number(input.categoryMedianPrice) || price || 1;
  const pv = Number(input.perceivedValue) || 0;

  // --- Sell-through ---
  const st = sellThroughProxy({ sold, active });
  const velocity = updateGammaPoisson(WEAK_VELOCITY_PRIOR, sold, windowDays);
  const dens = competitionDensity({ active, velocityPerDay: velocity.mean });

  const str = {
    rate: st.str,
    ci90: [st.low, st.high],
    confidence: soldMissing ? st.confidence * 0.35 : st.confidence,
    sold,
    active,
    windowDays,
    source: soldMissing ? "synthetic_or_active_only" : "sold_over_active_plus_sold",
    caveat: soldMissing
      ? "Sold evidence missing — STR is weak/synthetic until Insights or Terapeak pack"
      : null,
  };

  // --- CTR proxy (NOT official eBay CTR) ---
  // Engagement intensity from watches + price attractiveness + title signal length clamp
  const priceAttract = price > 0 ? clamp(1 - Math.abs(Math.log((price + 1) / (median + 1))) / 2, 0, 1) : 0.3;
  const watchNorm =
    watches == null ? null : clamp(Math.log10(watches + 1) / Math.log10(500 + 1), 0, 1);
  const titleLen = String(input.title || "").length;
  const titleSignal = clamp(titleLen / 80, 0.2, 1) * (pv > 0 ? 0.7 + 0.3 * pv : 0.7);

  // Relative impression proxy: denser markets → more impressions, lower CTR chance
  const impressionProxy = clamp(Math.log10(active + 10) / 4, 0.15, 1);
  const engagement = watchNorm != null ? 0.55 * watchNorm + 0.25 * priceAttract + 0.2 * titleSignal : 0.35 * priceAttract + 0.35 * titleSignal + 0.3 * (1 - Math.min(dens.density / 800, 1));
  const ctrProxy = clamp(engagement / Math.max(impressionProxy, 0.2), 0, 1) * 0.12; // scale to ~0–12% band

  const ctr = {
    rate: Math.round(ctrProxy * 10000) / 10000,
    ratePct: Math.round(ctrProxy * 10000) / 100,
    source: "proxy_engagement",
    inputs: {
      watchCount: watches,
      watchNorm,
      priceAttract: round4(priceAttract),
      titleSignal: round4(titleSignal),
      impressionProxy: round4(impressionProxy),
    },
    caveat: "Not official eBay CTR — proxy from watches/price/title/competition only",
  };

  // --- Popularity ---
  const popularity = clamp(
    0.35 * (watchNorm ?? st.confidence * 0.5) +
      0.3 * st.str +
      0.2 * clamp(velocity.mean / 2, 0, 1) +
      0.15 * pv,
    0,
    1
  );

  // --- Rank within sample ---
  const sampleSize = Number(input.sampleSize) || active || 1;
  let percentile = null;
  if (input.sampleIndex != null && sampleSize > 0) {
    percentile = 1 - Number(input.sampleIndex) / sampleSize;
  }
  const marketRank = {
    sampleSize,
    sampleIndex: input.sampleIndex ?? null,
    percentile: percentile != null ? round4(percentile) : null,
    density: dens.density,
    velocityPerDay: round4(velocity.mean),
    velocityCi90: velocity.ci90.map(round4),
  };

  // --- Purchase history ---
  const soldComps = Array.isArray(input.soldComps) ? input.soldComps : [];
  const purchaseHistory = {
    available: soldComps.length > 0,
    count: soldComps.length,
    source: soldComps.length ? soldComps[0].source || "ebay_marketplace_insights" : null,
    events: soldComps.slice(0, 50).map(normalizePurchaseEvent),
    caveat: soldComps.length
      ? null
      : "No purchase/sold history on this keyset — paste Terapeak pack or entitle Insights",
  };

  return {
    sellThrough: str,
    ctr,
    popularity: round4(popularity),
    marketRank,
    purchaseHistory,
    watches: watches,
    computedAt: new Date().toISOString(),
  };
}

function normalizePurchaseEvent(e) {
  return {
    date: e.date || e.soldDate || e.listingDate || null,
    price: e.price != null ? Number(e.price) : null,
    title: e.title || null,
    url: e.url || null,
    condition: e.grade || e.condition || null,
    kind: e.kind || "sold",
    id: e.id || null,
    source: e.source || null,
  };
}

function clamp(x, lo, hi) {
  return Math.min(hi, Math.max(lo, x));
}
function round4(x) {
  return Math.round(Number(x) * 10000) / 10000;
}
