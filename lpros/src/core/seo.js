/**
 * Title / keyword swarm + SEO competition scoring.
 * Generates hundreds of title variants, mines buyer-language patterns,
 * and scores vs competitor corpus for outrank potential.
 */
import { psychProxies } from "./psychology.js";

const MATERIALS = [
  "solid wood",
  "oak",
  "walnut",
  "bamboo",
  "hardwood",
  "stainless steel",
  "aluminum",
  "metal",
  "leather",
];
const USE_CASES = [
  "desk",
  "office",
  "home office",
  "workspace",
  "drawer",
  "under desk",
  "desktop",
  "vanity",
  "kitchen",
  "garage",
];
const BENEFITS = [
  "organizer",
  "clutter solution",
  "cable management",
  "storage tray",
  "mail sorter",
  "letter tray",
  "file rack",
  "upgrade",
  "heavy duty",
  "no-drill",
  "modular",
  "stackable",
  "adjustable",
];
const MODIFIERS = [
  "premium",
  "minimalist",
  "professional",
  "compact",
  "large",
  "with drawers",
  "with slots",
  "multi-tier",
  "5 tray",
  "6 slot",
  "vintage",
  "modern",
];

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
  "free",
  "shipping",
  "set",
  "pcs",
  "lot",
]);

/**
 * Mine keywords + buyer patterns from competitor titles.
 */
export function mineKeywordPatterns(titles = []) {
  const unigrams = new Map();
  const bigrams = new Map();
  const materials = new Map();
  const benefits = new Map();

  for (const raw of titles) {
    const t = String(raw || "").toLowerCase();
    const tokens = t
      .replace(/[^a-z0-9\s-]/g, " ")
      .split(/\s+/)
      .filter((w) => w.length > 2 && !STOP.has(w));

    for (const w of tokens) unigrams.set(w, (unigrams.get(w) || 0) + 1);
    for (let i = 0; i < tokens.length - 1; i++) {
      const bg = `${tokens[i]} ${tokens[i + 1]}`;
      bigrams.set(bg, (bigrams.get(bg) || 0) + 1);
    }
    for (const m of MATERIALS) if (t.includes(m)) materials.set(m, (materials.get(m) || 0) + 1);
    for (const b of BENEFITS) if (t.includes(b)) benefits.set(b, (benefits.get(b) || 0) + 1);
  }

  const top = (map, n = 25) =>
    [...map.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, n)
      .map(([term, count]) => ({
        term,
        count,
        share: titles.length ? count / titles.length : 0,
      }));

  return {
    sampleSize: titles.length,
    topUnigrams: top(unigrams, 40),
    topBigrams: top(bigrams, 30),
    materialDemand: top(materials, 12),
    benefitDemand: top(benefits, 12),
    buyerLanguage: inferBuyerLanguage(top(unigrams, 20), top(benefits, 10)),
  };
}

function inferBuyerLanguage(unigrams, benefits) {
  const cues = [];
  if (benefits.some((b) => /clutter|organiz|cable|storage/.test(b.term))) {
    cues.push("problem-solve / clutter reduction language wins share");
  }
  if (unigrams.some((u) => /oak|walnut|bamboo|wood|steel/.test(u.term))) {
    cues.push("material keywords correlate with higher perceived value listings");
  }
  if (unigrams.some((u) => /vintage|rustic/.test(u.term))) {
    cues.push("aesthetic/vintage modifiers present — differentiation lane");
  }
  if (unigrams.some((u) => /free|hot|sale|pcs/.test(u.term))) {
    cues.push("spam/clickbait tokens in corpus — avoid for trust CTR");
  }
  return cues;
}

/**
 * Generate title variations (deterministic combinatorial swarm).
 */
export function generateTitleVariations({
  seed = "desk organizer",
  categoryHint = "organizer",
  maxTitles = 200,
  patterns = null,
} = {}) {
  const seedClean = String(seed).trim();
  const hotMaterials = (patterns?.materialDemand || []).map((m) => m.term);
  const hotBenefits = (patterns?.benefitDemand || []).map((b) => b.term);
  const materials = unique([...(hotMaterials.length ? hotMaterials : []), ...MATERIALS]);
  const benefits = unique([...(hotBenefits.length ? hotBenefits : []), ...BENEFITS]);
  const useCases = USE_CASES;
  const modifiers = MODIFIERS;

  const out = [];
  const seen = new Set();
  const push = (title, meta) => {
    const t = title.replace(/\s+/g, " ").trim().slice(0, 80);
    const key = t.toLowerCase();
    if (!t || seen.has(key)) return;
    seen.add(key);
    out.push({ title: t, ...meta });
  };

  // Seed itself + light expansions
  push(seedClean, { family: "seed", keywords: tokenize(seedClean) });

  for (const mat of materials) {
    for (const use of useCases) {
      for (const ben of benefits.slice(0, 8)) {
        push(`${mat} ${use} ${ben}`, {
          family: "material_use_benefit",
          keywords: [mat, use, ben],
        });
        push(`${use} ${ben} ${mat} upgrade`, {
          family: "use_benefit_upgrade",
          keywords: [use, ben, mat, "upgrade"],
        });
        if (out.length >= maxTitles) return finalize(out, categoryHint);
      }
    }
  }

  for (const mod of modifiers) {
    for (const mat of materials.slice(0, 6)) {
      for (const ben of benefits.slice(0, 6)) {
        push(`${mod} ${mat} ${seedClean} ${ben}`.replace(new RegExp(`\\b${categoryHint}\\b`, "ig"), categoryHint), {
          family: "modifier_stack",
          keywords: [mod, mat, ben],
        });
        if (out.length >= maxTitles) return finalize(out, categoryHint);
      }
    }
  }

  // Bigram-led from mined patterns
  for (const bg of patterns?.topBigrams || []) {
    for (const mat of materials.slice(0, 4)) {
      push(`${mat} ${bg.term} organizer`, {
        family: "mined_bigram",
        keywords: [mat, ...bg.term.split(" ")],
      });
      if (out.length >= maxTitles) return finalize(out, categoryHint);
    }
  }

  return finalize(out.slice(0, maxTitles), categoryHint);
}

function finalize(list, categoryHint) {
  return list.map((row, i) => {
    const psych = psychProxies({
      title: row.title,
      salePrice: 49,
      categoryMedianPrice: 45,
    });
    return {
      id: `TV-${i + 1}`,
      ...row,
      categoryHint,
      scammy: psych.scammy,
      perceivedValue: psych.perceivedValue,
      psychFit: psych.psychFit,
      scamHits: psych.scamHits,
    };
  });
}

/**
 * Score a title vs competitor keyword corpus for SEO / outrank potential.
 */
export function scoreTitleSeo(title, patterns, opts = {}) {
  const t = String(title).toLowerCase();
  const tokens = tokenize(t);
  const uni = new Map((patterns?.topUnigrams || []).map((u) => [u.term, u.share]));
  const bi = new Map((patterns?.topBigrams || []).map((u) => [u.term, u.share]));

  let coverage = 0;
  let covered = 0;
  for (const [term, share] of uni) {
    if (t.includes(term)) {
      coverage += share;
      covered += 1;
    }
  }
  let bigramHits = 0;
  for (const [term, share] of bi) {
    if (t.includes(term)) {
      coverage += share * 1.4;
      bigramHits += 1;
    }
  }

  const psych = psychProxies({
    title,
    salePrice: opts.salePrice ?? 49,
    categoryMedianPrice: opts.categoryMedianPrice ?? 45,
  });

  // Differentiation: not a clone of the single most common title shape
  const lengthScore = clamp(title.length / 75, 0.3, 1);
  const materialHit = MATERIALS.some((m) => t.includes(m)) ? 1 : 0;
  const spamPenalty = psych.scammy ? 0.2 : 1;

  const seoScore = clamp(
    (0.35 * clamp(coverage, 0, 1.5) +
      0.2 * clamp(covered / 8, 0, 1) +
      0.15 * clamp(bigramHits / 3, 0, 1) +
      0.15 * psych.perceivedValue +
      0.1 * lengthScore +
      0.05 * materialHit) *
      spamPenalty,
    0,
    1
  );

  return {
    seoScore: round4(seoScore),
    keywordCoverage: round4(coverage),
    coveredUnigrams: covered,
    bigramHits,
    materialHit: Boolean(materialHit),
    perceivedValue: psych.perceivedValue,
    scammy: psych.scammy,
    tokens,
    outrankAdvice: buildOutrankAdvice({ covered, bigramHits, materialHit, psych, t }),
  };
}

function buildOutrankAdvice({ covered, bigramHits, materialHit, psych, t }) {
  const tips = [];
  if (covered < 4) tips.push("Add 2–3 high-share category unigrams from mined list");
  if (bigramHits < 1) tips.push("Include at least one high-share bigram buyers already search");
  if (!materialHit) tips.push("Lead with material (oak/walnut/bamboo/steel) for PV + CTR");
  if (!/upgrade|heavy|clutter|organiz/.test(t)) tips.push("Add problem-solve or upgrade verbage");
  if (psych.scammy) tips.push("Remove spam/qty/clickbait tokens — they kill trust CTR");
  if (tips.length === 0) tips.push("Title is competitive — pair with lifestyle hero image + benefit-first description");
  return tips;
}

/**
 * Image optimization checklist / score (URL heuristics — no CV model required).
 */
export function scoreImageSeo(images = [], opts = {}) {
  const list = (images || []).filter(Boolean);
  const count = list.length;
  const hasHttps = list.length === 0 || list.every((u) => /^https:\/\//i.test(u));
  const score = clamp(
    0.35 * clamp(count / 6, 0, 1) +
      0.25 * (hasHttps ? 1 : 0.4) +
      0.2 * (count >= 1 ? 1 : 0) +
      0.2 * (opts.hasLifestyle ? 1 : 0.4),
    0,
    1
  );
  return {
    imageScore: round4(score),
    imageCount: count,
    hasHttps,
    recommendations: [
      count < 6 ? `Add ${6 - count} more photos (scale, in-use, detail, packaging)` : "Gallery depth OK",
      "Hero: lifestyle desk shot for buyer attachment / CTR",
      "Image 2: dimensions / slots overlay",
      "Image 3: material close-up (grain/steel)",
      "Avoid watermark spam and stock-looking white-void only sets",
      "Filename/alt text later: include primary keyword + material",
    ],
  };
}

/**
 * Planning checklist for listing images (pre-shoot) — buyer attachment + CTR.
 */
export function imageSeoChecklist({ title, primaryKeyword } = {}) {
  const kw = primaryKeyword || tokenize(title || "").slice(0, 3).join(" ");
  const checks = [
    { id: "hero_lifestyle", ok: false, tip: `Hero lifestyle shot including "${kw}" context` },
    { id: "gallery_depth_8", ok: false, tip: "Ship 8+ images (scale, in-use, detail, packaging)" },
    { id: "material_closeup", ok: false, tip: "Material grain/texture close-up for PV" },
    { id: "dimensions_overlay", ok: false, tip: "Dimensions / slot count overlay for trust CTR" },
    { id: "no_watermark_spam", ok: true, tip: "No watermark spam or stock white-void only" },
    { id: "keyword_filename", ok: false, tip: `Filename/alt later: ${kw}` },
  ];
  const done = checks.filter((c) => c.ok).length;
  return {
    score: Math.round((done / checks.length) * 100),
    imageScore: round4(done / checks.length),
    checks,
    recommendations: checks.filter((c) => !c.ok).map((c) => c.tip),
  };
}

/**
 * Pull primary + secondary keywords for a scored title.
 */
export function extractKeywordsFromTitle(title, patterns = null) {
  const tokens = tokenize(title || "");
  const hot = (patterns?.topUnigrams || []).map((u) => u.term);
  const primary =
    hot.find((t) => String(title || "").toLowerCase().includes(t)) ||
    tokens.slice(0, 3).join(" ") ||
    String(title || "").slice(0, 40);
  const secondary = unique([
    ...hot.filter((t) => String(title || "").toLowerCase().includes(t) && t !== primary).slice(0, 6),
    ...tokens.filter((t) => t !== primary).slice(0, 6),
  ]).slice(0, 8);
  return { primaryKeyword: primary, secondaryKeywords: secondary };
}

/**
 * Optimal description scaffold aimed at conversion.
 */
export function buildConversionDescription({ title, keywords = [], material, problem, price } = {}) {
  const kw = unique(keywords).slice(0, 8).join(", ");
  const bullets = [
    problem
      ? `Solves ${problem} — less desk chaos, faster reach to what you need`
      : "Cuts desk clutter so daily work stays visible and calm",
    material
      ? `${material} build — higher perceived quality than thin plastic trays`
      : "Durable build meant for daily office use",
    "Clear compartments — measure your desk; sizes in Item Specifics",
    "Gift-ready for home office upgrades",
    "Ships packed for protection — message within 24h if damaged",
  ];
  return {
    title: String(title || "").slice(0, 80),
    keywords: unique(keywords).slice(0, 12),
    bullets,
    descriptionText: [
      title,
      "",
      bullets.map((b) => `• ${b}`).join("\n"),
      "",
      kw ? `Search-friendly details: ${kw}` : "",
      price != null ? `Competitive research band near $${Number(price).toFixed(2)} (verify sold comps).` : "",
      "Wholesale fulfillment — not retail arbitrage.",
    ]
      .filter(Boolean)
      .join("\n"),
  };
}

function tokenize(t) {
  return String(t)
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOP.has(w));
}
function unique(arr) {
  return [...new Set(arr.filter(Boolean))];
}
function clamp(x, lo, hi) {
  return Math.min(hi, Math.max(lo, x));
}
function round4(x) {
  return Math.round(Number(x) * 10000) / 10000;
}
