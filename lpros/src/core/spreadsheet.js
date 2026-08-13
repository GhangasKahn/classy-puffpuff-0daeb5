/**
 * Spreadsheet / CSV export for orchestration decision tracking.
 */

export function csvEscape(v) {
  if (v == null) return "";
  const s = String(v);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function rowsToCsv(rows, columns) {
  const header = columns.map((c) => csvEscape(c.label || c.key)).join(",");
  const lines = rows.map((row) =>
    columns
      .map((c) => csvEscape(typeof c.value === "function" ? c.value(row) : row[c.key]))
      .join(",")
  );
  return [header, ...lines].join("\n") + "\n";
}

/** Decision sheet columns for title/keyword tests. */
export const DECISION_COLUMNS = [
  { key: "rank", label: "rank" },
  { key: "testPriority", label: "test_priority" },
  { key: "decision", label: "decision" },
  { key: "title", label: "title" },
  { key: "seoScore", label: "seo_score" },
  { key: "primaryKeyword", label: "primary_keyword" },
  {
    key: "secondaryKeywords",
    label: "secondary_keywords",
    value: (r) => (r.secondaryKeywords || []).join(" | "),
  },
  { key: "categoryId", label: "category_id" },
  { key: "categoryPath", label: "category_path" },
  { key: "suggestedPrice", label: "suggested_price" },
  { key: "landedCost", label: "landed_cost" },
  { key: "estFees", label: "est_fees" },
  { key: "estNet", label: "est_net" },
  { key: "estMarginPct", label: "est_margin_pct" },
  { key: "competitionProxy", label: "competition_proxy" },
  { key: "liveTotal", label: "live_total_results" },
  { key: "liveMedianPrice", label: "live_median_price" },
  { key: "liveImageCoverage", label: "live_image_coverage" },
  { key: "imageSeoScore", label: "image_seo_score" },
  {
    key: "imageActions",
    label: "image_actions",
    value: (r) => (r.imageActions || []).join(" | "),
  },
  { key: "descriptionOutline", label: "description_outline" },
  { key: "outrankNotes", label: "outrank_notes" },
  {
    key: "buyerAttachmentHooks",
    label: "buyer_hooks",
    value: (r) => (r.buyerHooks || []).join(" | "),
  },
  { key: "variantFamily", label: "variant_family" },
  { key: "sourceQuery", label: "source_query" },
  { key: "jobId", label: "job_id" },
  { key: "loggedAt", label: "logged_at" },
];

export function decisionForRow(row) {
  if (row.testPriority === "A" && (row.seoScore || 0) >= 62) return "TEST_NOW";
  if (row.testPriority === "B") return "TEST_AFTER_A";
  if ((row.seoScore || 0) < 45) return "REWRITE";
  if ((row.liveTotal || 0) > 8000 && (row.seoScore || 0) < 70) return "NARROW_KEYWORD";
  return "PARK";
}

function outrankNotes(row) {
  const notes = [];
  if ((row.liveTotal || 0) > 5000) {
    notes.push("High competition — differentiate with material+use-case frontload");
  }
  if ((row.liveImageCoverage || 1) < 0.85) {
    notes.push("Competitors weak on images — win with 8+ lifestyle+detail shots");
  }
  if ((row.seoScore || 0) >= 70) {
    notes.push("Strong SEO scaffold — A/B price and hero image CTR");
  }
  if (!notes.length) notes.push("Probe top 3 comps; match length and attribute density");
  return notes.join("; ");
}

export function enrichDecisionRows(rows, meta = {}) {
  return rows.map((r, i) => {
    const row = {
      ...r,
      rank: i + 1,
      jobId: meta.jobId || r.jobId || "",
      loggedAt: meta.loggedAt || new Date().toISOString(),
      sourceQuery: meta.query || r.sourceQuery || "",
      categoryId: meta.categoryId || r.categoryId || "",
      categoryPath: meta.categoryPath || r.categoryPath || "",
      landedCost: meta.landedCost ?? r.landedCost,
      suggestedPrice: r.suggestedPrice ?? meta.suggestedPrice,
      estFees: r.estFees,
      estNet: r.estNet,
      estMarginPct: r.estMarginPct,
      imageSeoScore: r.imageSeo?.score ?? r.imageSeo?.imageScore,
      imageActions:
        r.imageActions ||
        (r.imageSeo?.checks || []).filter((c) => !c.ok).map((c) => c.id) ||
        (r.imageSeo?.recommendations || []).slice(0, 4),
      descriptionOutline:
        r.descriptionOutline ||
        r.description?.bullets?.slice(0, 3).join(" > ") ||
        (r.description?.descriptionText || "").slice(0, 120),
      buyerHooks: r.buyerHooks || r.description?.bullets?.slice(0, 3) || [],
      secondaryKeywords: r.secondaryKeywords || [],
    };
    row.outrankNotes = outrankNotes(row);
    row.decision = decisionForRow(row);
    return row;
  });
}

export function toDecisionCsv(rows, meta = {}) {
  const enriched = enrichDecisionRows(rows, meta);
  return {
    csv: rowsToCsv(enriched, DECISION_COLUMNS),
    rows: enriched,
    columns: DECISION_COLUMNS.map((c) => c.label || c.key),
  };
}
