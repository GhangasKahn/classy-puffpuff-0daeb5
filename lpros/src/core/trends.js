/**
 * Trend / momentum analysis from Browse snapshots.
 * Compares newlyListed vs bestMatch corpora + cross-category rollups.
 * Honest: not official eBay Trends — derived from live listing language & density.
 */

function tokenize(t) {
  return String(t || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 2);
}

function countTerms(titles = [], n = 40) {
  const uni = new Map();
  const bi = new Map();
  for (const raw of titles) {
    const toks = tokenize(raw);
    for (const w of toks) uni.set(w, (uni.get(w) || 0) + 1);
    for (let i = 0; i < toks.length - 1; i++) {
      const bg = `${toks[i]} ${toks[i + 1]}`;
      bi.set(bg, (bi.get(bg) || 0) + 1);
    }
  }
  const top = (map, lim) =>
    [...map.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, lim)
      .map(([term, count]) => ({
        term,
        count,
        share: titles.length ? count / titles.length : 0,
      }));
  return { unigrams: top(uni, n), bigrams: top(bi, Math.floor(n * 0.75)), sampleSize: titles.length };
}

/**
 * Rising terms = high share in "fresh" (newlyListed) vs baseline (bestMatch/overall).
 */
export function keywordMomentum({ freshTitles = [], baselineTitles = [], minFresh = 3 } = {}) {
  const fresh = countTerms(freshTitles, 50);
  const base = countTerms(baselineTitles, 50);
  const baseMap = new Map(base.unigrams.map((u) => [u.term, u.share]));
  const rising = [];
  const falling = [];
  for (const u of fresh.unigrams) {
    if (u.count < minFresh) continue;
    const bShare = baseMap.get(u.term) || 0;
    const lift = bShare > 0 ? u.share / bShare : u.share > 0 ? 3 : 0;
    const delta = u.share - bShare;
    const row = {
      term: u.term,
      freshShare: round4(u.share),
      baselineShare: round4(bShare),
      lift: round4(lift),
      delta: round4(delta),
      freshCount: u.count,
    };
    if (lift >= 1.35 && delta > 0.02) rising.push(row);
    else if (lift <= 0.65 && bShare > 0.05) falling.push(row);
  }
  rising.sort((a, b) => b.lift - a.lift || b.delta - a.delta);
  falling.sort((a, b) => a.lift - b.lift);
  return {
    method: "newlyListed_vs_bestMatch_title_share",
    caveat: "Proxy momentum from active listing language — not official eBay Trends or sold velocity",
    freshSample: fresh.sampleSize,
    baselineSample: base.sampleSize,
    rising: rising.slice(0, 25),
    falling: falling.slice(0, 15),
    freshBigrams: fresh.bigrams.slice(0, 15),
  };
}

/**
 * Price pressure + competition density snapshot for a category lane.
 */
export function categoryTrendSnapshot({
  categoryId,
  label,
  query,
  activeTotal,
  sampleSize,
  priceLadder,
  newlyListedMedian,
  bestMatchMedian,
  sellerHhi,
  density,
  productCount,
  avgImageCount,
  topKeywords = [],
} = {}) {
  const p50 = priceLadder?.p50 ?? null;
  const p90 = priceLadder?.p90 ?? null;
  const p10 = priceLadder?.p10 ?? null;
  const spread =
    p90 != null && p10 != null && p50 ? round4((p90 - p10) / Math.max(p50, 1)) : null;
  const freshPremium =
    newlyListedMedian != null && bestMatchMedian != null && bestMatchMedian > 0
      ? round4(newlyListedMedian / bestMatchMedian - 1)
      : null;

  let heat = 0;
  if (activeTotal != null) heat += Math.min(40, activeTotal / 200);
  if (density != null) heat += Math.min(25, Number(density) / 4);
  if (freshPremium != null && freshPremium > 0) heat += Math.min(20, freshPremium * 100);
  if (avgImageCount != null) heat += Math.min(15, avgImageCount * 1.5);
  heat = Math.round(Math.min(100, heat));

  return {
    categoryId,
    label,
    query,
    activeTotal: activeTotal ?? null,
    sampleSize: sampleSize ?? null,
    productCount: productCount ?? null,
    priceLadder: priceLadder || null,
    priceSpread: spread,
    newlyListedMedian: newlyListedMedian ?? null,
    bestMatchMedian: bestMatchMedian ?? null,
    freshPricePremium: freshPremium,
    sellerHhi: sellerHhi ?? null,
    density: density ?? null,
    avgImageCount: avgImageCount ?? null,
    heatScore: heat,
    topKeywords: topKeywords.slice(0, 12),
    read:
      heat >= 70
        ? "Hot lane — high competition; win on differentiation + image CTR"
        : heat >= 40
          ? "Active lane — test rising keywords with premium materials"
          : "Quieter lane — fewer comps; validate demand with sold evidence",
  };
}

/**
 * Cross-category rollup + idea factory (100s of testable ideas).
 */
export function buildCampaignTrends({ lanes = [], ideasTarget = 200 } = {}) {
  const categorySnapshots = lanes.map((l) => l.snapshot).filter(Boolean);
  categorySnapshots.sort((a, b) => (b.heatScore || 0) - (a.heatScore || 0));

  const allRising = [];
  for (const lane of lanes) {
    for (const r of lane.momentum?.rising || []) {
      allRising.push({ ...r, categoryId: lane.categoryId, label: lane.label });
    }
  }
  allRising.sort((a, b) => b.lift - a.lift);

  const materialHits = new Map();
  const benefitHits = new Map();
  const MATERIALS = ["oak", "walnut", "bamboo", "wood", "steel", "leather", "acrylic"];
  const BENEFITS = ["organizer", "storage", "clutter", "cable", "tray", "stand", "riser", "drawer"];
  for (const lane of lanes) {
    for (const t of lane.titles || []) {
      const low = t.toLowerCase();
      for (const m of MATERIALS) if (low.includes(m)) materialHits.set(m, (materialHits.get(m) || 0) + 1);
      for (const b of BENEFITS) if (low.includes(b)) benefitHits.set(b, (benefitHits.get(b) || 0) + 1);
    }
  }

  const risingTerms = unique([
    ...allRising.map((r) => r.term),
    "modular",
    "minimalist",
    "premium",
    "compact",
    "stackable",
    "cable",
    "clutter",
  ]).slice(0, 24);
  const materials = unique([
    ...[...materialHits.entries()].sort((a, b) => b[1] - a[1]).map(([t]) => t),
    "oak",
    "walnut",
    "bamboo",
    "wood",
    "steel",
  ]);
  const benefits = unique([
    ...[...benefitHits.entries()].sort((a, b) => b[1] - a[1]).map(([t]) => t),
    "organizer",
    "storage",
    "tray",
    "stand",
    "riser",
  ]);
  const hotCats = categorySnapshots.length
    ? categorySnapshots.slice(0, 5)
    : lanes.map((l) => ({
        categoryId: l.categoryId,
        label: l.label,
        heatScore: 40,
      }));

  const ideas = [];
  const seen = new Set();
  const pushIdea = (idea) => {
    const key = idea.title.toLowerCase();
    if (seen.has(key) || ideas.length >= ideasTarget) return;
    seen.add(key);
    ideas.push(idea);
  };

  for (const cat of hotCats) {
    for (const mat of materials.slice(0, 8)) {
      for (const ben of benefits.slice(0, 8)) {
        for (const rise of risingTerms.slice(0, 12)) {
          pushIdea({
            title: `${mat} ${rise} ${ben}`.replace(/\s+/g, " ").trim().slice(0, 80),
            family: "trend_combo",
            categoryId: cat.categoryId,
            categoryLabel: cat.label,
            heatScore: cat.heatScore || 40,
            drivers: [mat, rise, ben],
            rationale: `Combo of rising/seed term "${rise}" × material × benefit in ${cat.label}`,
          });
          pushIdea({
            title: `${cat.label} ${mat} ${ben} ${rise}`.replace(/\s+/g, " ").trim().slice(0, 80),
            family: "category_frontload",
            categoryId: cat.categoryId,
            categoryLabel: cat.label,
            heatScore: cat.heatScore || 40,
            drivers: [cat.label, mat, ben],
            rationale: `Category-frontloaded idea for ${cat.label}`,
          });
          if (ideas.length >= ideasTarget) break;
        }
      }
    }
  }

  // Price-band ideas from ladder
  for (const cat of categorySnapshots) {
    const p50 = cat.priceLadder?.p50;
    if (p50 == null) continue;
    pushIdea({
      title: `${cat.label} under-$${Math.floor(p50)} value play`.slice(0, 80),
      family: "price_gap",
      categoryId: cat.categoryId,
      categoryLabel: cat.label,
      heatScore: cat.heatScore,
      drivers: ["price_gap", String(p50)],
      rationale: `Price below category median $${p50} — test conversion vs image quality`,
    });
    pushIdea({
      title: `${cat.label} premium above-$${Math.ceil((cat.priceLadder?.p75 || p50) * 1.05)}`.slice(0, 80),
      family: "premium_band",
      categoryId: cat.categoryId,
      categoryLabel: cat.label,
      heatScore: cat.heatScore,
      drivers: ["premium"],
      rationale: "Premium band — needs material proof + lifestyle gallery",
    });
  }

  return {
    generatedAt: new Date().toISOString(),
    caveat:
      "Trend heat/momentum are Browse-listing proxies (title language + density + fresh price). Sold/STR trends need Insights or Terapeak.",
    categoryHeat: categorySnapshots,
    hottestCategory: categorySnapshots[0] || null,
    risingKeywords: allRising.slice(0, 40),
    materialDemand: [...materialHits.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([term, count]) => ({ term, count })),
    benefitDemand: [...benefitHits.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([term, count]) => ({ term, count })),
    ideaCount: ideas.length,
    ideas: ideas.slice(0, ideasTarget),
  };
}

export function trendsToCsv(trends) {
  const lines = ["sheet,rank,field,value,meta"];
  const esc = (v) => {
    const s = String(v ?? "");
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  (trends.categoryHeat || []).forEach((c, i) => {
    lines.push(
      ["category_heat", i + 1, c.label || c.categoryId, c.heatScore, `active=${c.activeTotal};p50=${c.priceLadder?.p50}`]
        .map(esc)
        .join(",")
    );
  });
  (trends.risingKeywords || []).forEach((r, i) => {
    lines.push(
      ["rising_keyword", i + 1, r.term, r.lift, `cat=${r.label || r.categoryId};delta=${r.delta}`]
        .map(esc)
        .join(",")
    );
  });
  (trends.ideas || []).forEach((idea, i) => {
    lines.push(
      ["idea", i + 1, idea.title, idea.heatScore, `${idea.family}|${idea.categoryLabel}|${(idea.drivers || []).join("+")}`]
        .map(esc)
        .join(",")
    );
  });
  return lines.join("\n") + "\n";
}

function unique(arr) {
  return [...new Set(arr.filter(Boolean))];
}
function round4(x) {
  return Math.round(Number(x) * 10000) / 10000;
}
