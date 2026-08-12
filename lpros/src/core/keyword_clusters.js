/**
 * Keyword / idea clustering for A/B test families.
 * Groups titles into search-intent buckets so you test families, not 400 clones.
 */

const STOP = new Set([
  "the",
  "and",
  "for",
  "with",
  "from",
  "this",
  "that",
  "your",
  "new",
  "set",
]);

function tokenize(t) {
  return String(t || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOP.has(w));
}

function bigrams(tokens) {
  const out = [];
  for (let i = 0; i < tokens.length - 1; i++) out.push(`${tokens[i]} ${tokens[i + 1]}`);
  return out;
}

/**
 * Cluster titles/ideas by dominant bigram (fallback: first two tokens).
 */
export function clusterKeywords(rows = [], { maxClusters = 24, minSize = 2 } = {}) {
  const buckets = new Map();
  for (const row of rows) {
    const title = row.title || row.term || "";
    const toks = tokenize(title);
    const bgs = bigrams(toks);
    const key = bgs[0] || toks.slice(0, 2).join(" ") || title.slice(0, 24).toLowerCase();
    if (!key) continue;
    if (!buckets.has(key)) {
      buckets.set(key, {
        clusterId: `CL-${key.replace(/\s+/g, "-").slice(0, 28)}`,
        seed: key,
        members: [],
        categoryIds: new Set(),
        seoScores: [],
        heatScores: [],
      });
    }
    const b = buckets.get(key);
    b.members.push(row);
    if (row.categoryId) b.categoryIds.add(String(row.categoryId));
    if (row.seoScore != null) b.seoScores.push(Number(row.seoScore));
    if (row.heatScore != null) b.heatScores.push(Number(row.heatScore));
  }

  const clusters = [...buckets.values()]
    .map((b) => {
      const avg = (arr) => (arr.length ? arr.reduce((s, n) => s + n, 0) / arr.length : null);
      const uniqueTitles = [...new Set(b.members.map((m) => String(m.title || m.term || "").toLowerCase()))];
      return {
        clusterId: b.clusterId,
        seed: b.seed,
        size: b.members.length,
        uniqueTitles: uniqueTitles.length,
        categoryIds: [...b.categoryIds],
        avgSeo: avg(b.seoScores) != null ? Math.round(avg(b.seoScores)) : null,
        avgHeat: avg(b.heatScores) != null ? Math.round(avg(b.heatScores)) : null,
        testPlan: recommendTestPlan(b.members.length, uniqueTitles.length),
        sampleTitles: uniqueTitles.slice(0, 6),
      };
    })
    .filter((c) => c.size >= minSize || c.uniqueTitles >= 1)
    .sort((a, b) => (b.avgSeo || 0) - (a.avgSeo || 0) || b.size - a.size)
    .slice(0, maxClusters);

  return {
    clusterCount: clusters.length,
    clusteredRows: rows.length,
    clusters,
    note: "Test 2–3 titles per cluster (not every clone). Winner stays; losers recycle keywords.",
  };
}

function recommendTestPlan(size, unique) {
  const n = Math.min(3, Math.max(1, unique >= 6 ? 3 : unique >= 3 ? 2 : 1));
  return {
    listingsToTest: n,
    holdouts: Math.max(0, unique - n),
    rationale:
      n === 1
        ? "Thin cluster — one listing, watch STR 14d"
        : `A/B ${n} titles in this intent bucket; kill after 14d if no watch/sale proxy`,
  };
}

/**
 * Score an idea vs competitor corpus uniqueness + heat.
 */
export function scoreIdea(idea, { competitorTitles = [], heatScore = 40 } = {}) {
  const toks = new Set(tokenize(idea.title || idea.term));
  let overlap = 0;
  let compared = 0;
  for (const t of competitorTitles.slice(0, 80)) {
    const ct = new Set(tokenize(t));
    if (!ct.size) continue;
    compared += 1;
    const hit = [...toks].filter((w) => ct.has(w)).length;
    overlap += hit / Math.max(toks.size, 1);
  }
  const cloneRisk = compared ? overlap / compared : 0.5;
  const uniqueness = Math.max(0, 1 - cloneRisk);
  const score = Math.round(
    100 * (0.45 * uniqueness + 0.35 * Math.min(1, (heatScore || 40) / 100) + 0.2 * Math.min(1, toks.size / 6))
  );
  return {
    ideaScore: score,
    uniqueness: Math.round(uniqueness * 100) / 100,
    cloneRisk: Math.round(cloneRisk * 100) / 100,
    decision: score >= 62 && uniqueness >= 0.35 ? "TEST_NOW" : score >= 45 ? "TEST_AFTER_A" : "PARK",
  };
}
