/**
 * Competitor / market intel — ZIK-style views from official Browse data.
 * Density, price ladder, seller concentration, listing freshness proxies.
 */
import { searchActiveListings } from "../../../ebay-sold-items/src/ebay/browse.js";
import { sellThroughProxy, competitionDensity } from "../../../lpros/src/core/bayesian.js";
import { psychProxies } from "../../../lpros/src/core/psychology.js";
import { netProfitPerSale } from "../../../lpros/src/core/economics.js";

export async function competitorIntel({
  q,
  categoryId,
  minPrice = 35,
  maxPrice = 200,
  limit = 100,
  productCostRatio = 0.4,
} = {}) {
  const page = await searchActiveListings({
    q,
    categoryIds: categoryId,
    minPrice,
    maxPrice,
    limit: Math.min(limit, 200),
    sort: "price",
  });

  // Defense in depth: Browse price filter is best-effort; enforce band locally
  const items = (page.items || []).filter(
    (i) => i.price != null && i.price >= minPrice && i.price <= maxPrice
  );
  const prices = items.map((i) => i.price).filter((p) => p > 0).sort((a, b) => a - b);
  const sellers = new Map();
  for (const it of items) {
    const s = it.seller || "unknown";
    if (!sellers.has(s)) sellers.set(s, { seller: s, count: 0, prices: [] });
    const row = sellers.get(s);
    row.count += 1;
    if (it.price != null) row.prices.push(it.price);
  }

  const sellerRows = [...sellers.values()]
    .map((s) => ({
      seller: s.seller,
      listings: s.count,
      share: items.length ? s.count / items.length : 0,
      medianPrice: median(s.prices),
    }))
    .sort((a, b) => b.listings - a.listings);

  const hhi = sellerRows.reduce((acc, s) => acc + s.share * s.share, 0);
  const dens = competitionDensity({
    active: page.total || items.length,
    velocityPerDay: Math.max(1, (page.total || items.length) * 0.01),
  });

  // Synthetic sold proxy until Insights entitled — mark as weak
  const st = sellThroughProxy({
    sold: Math.round((page.total || 0) * 0.05),
    active: page.total || items.length,
  });

  const ladder = {
    p10: percentile(prices, 0.1),
    p25: percentile(prices, 0.25),
    p50: percentile(prices, 0.5),
    p75: percentile(prices, 0.75),
    p90: percentile(prices, 0.9),
  };

  const scored = items.slice(0, 40).map((it) => {
    const psych = psychProxies({ title: it.title, salePrice: it.price, categoryMedianPrice: ladder.p50 });
    const cost = (it.price || 0) * productCostRatio;
    const econ = netProfitPerSale({
      salePrice: it.price || 0,
      productCost: cost,
      returnsBufferRate: 0.04,
    });
    return {
      id: it.id,
      title: it.title,
      price: it.price,
      seller: it.seller,
      url: it.url,
      condition: it.condition,
      perceivedValue: psych.perceivedValue,
      scammy: psych.scammy,
      psychFit: psych.psychFit,
      netAtCostRatio: econ.net,
      marginPct: econ.marginPct,
    };
  });

  const lethal = scored
    .filter((s) => !s.scammy && s.perceivedValue >= 0.25 && s.netAtCostRatio > 0 && s.price >= minPrice)
    .sort((a, b) => b.perceivedValue * b.netAtCostRatio - a.perceivedValue * a.netAtCostRatio);

  return {
    query: q || null,
    categoryId: categoryId || null,
    priceBand: { min: minPrice, max: maxPrice },
    market: {
      activeTotal: page.total,
      sampleSize: items.length,
      priceLadder: ladder,
      density: dens.density,
      sellThroughProxy: { ...st, caveat: "Synthetic until Marketplace Insights entitled" },
      sellerConcentrationHHI: Math.round(hhi * 10000) / 10000,
      topSellers: sellerRows.slice(0, 12),
    },
    lethalCandidates: lethal.slice(0, 20),
    rejectedScamSample: scored.filter((s) => s.scammy).slice(0, 8),
    vsZik: {
      parity: ["active competition snapshot", "price distribution", "seller share"],
      superior: [
        "true fee/net economics (cash-is-truth)",
        "scam/red-flag kill filters",
        "perceived-value / upgrade / problem-solve scoring",
        "zero-trust multi-factor gates",
      ],
      gap: ["official sold/STR history requires Insights or Terapeak browser assist"],
    },
  };
}

function median(a) {
  if (!a?.length) return null;
  const s = [...a].sort((x, y) => x - y);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}
function percentile(a, p) {
  if (!a?.length) return null;
  const idx = Math.min(a.length - 1, Math.max(0, Math.floor(a.length * p)));
  return a[idx];
}
