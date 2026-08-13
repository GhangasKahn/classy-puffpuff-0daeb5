/**
 * Listing factory — turn researched comps + winning titles into testable packages.
 * Uses competitor item specifics / description language (not photos).
 */
import { draftListing } from "../agents/listing.js";
import { netProfitPerSale } from "./economics.js";
import { imageSeoChecklist, scoreTitleSeo, extractKeywordsFromTitle } from "./seo.js";
import { extractContentSignals } from "./listing_content.js";
import { clusterKeywords, scoreIdea } from "./keyword_clusters.js";

function mostCommonSpecifics(products = []) {
  const counts = new Map(); // name -> Map(value -> n)
  for (const p of products) {
    const spec = p.itemSpecifics || {};
    for (const [k, v] of Object.entries(spec)) {
      if (!k || v == null || String(v).length > 80) continue;
      if (!counts.has(k)) counts.set(k, new Map());
      const vm = counts.get(k);
      const val = String(v);
      vm.set(val, (vm.get(val) || 0) + 1);
    }
  }
  const out = {};
  for (const [k, vm] of counts) {
    const best = [...vm.entries()].sort((a, b) => b[1] - a[1])[0];
    if (best && best[1] >= 2) out[k] = best[0];
  }
  return out;
}

function competitorImageStats(products = []) {
  const counts = products.map((p) => Number(p.imageCount) || 0);
  const withImg = products.filter((p) => p.image).length;
  const avg = counts.length ? counts.reduce((s, n) => s + n, 0) / counts.length : 0;
  const max = counts.length ? Math.max(...counts) : 0;
  return {
    sample: products.length,
    withImages: withImg,
    avgImageCount: Math.round(avg * 10) / 10,
    maxImageCount: max,
    beatWith: Math.max(8, Math.ceil(avg) + 2),
    gap: avg < 6 ? "Competitors thin on gallery — lifestyle+detail wins CTR" : "Match 8+ then add lifestyle hero",
  };
}

function mergeSpecifics(base, competitorCommon, title) {
  const draft = draftListing({ title });
  return {
    ...draft.itemSpecifics,
    ...competitorCommon,
    ...base,
  };
}

function conversionCopy({ title, keywords, material, price, competitorExcerpts = [], signals = [] }) {
  const excerptCue = competitorExcerpts
    .map((e) => String(e || ""))
    .filter((e) => e.length > 40)
    .slice(0, 3);
  const problem = signals.includes("problem_solve")
    ? "desk / drawer clutter"
    : signals.includes("use_case_clear")
      ? "home-office setup friction"
      : "everyday workspace mess";
  const bullets = [
    `Solves ${problem} — one station instead of scattered trays and piles`,
    material
      ? `${material} build for perceived quality vs thin plastic organizers`
      : "Durable daily-use build — not a disposable pack",
    "Measure first — dimensions and compartments in Item Specifics",
    signals.includes("size_trust")
      ? "Size callouts in photos (overlay) so buyers trust the fit"
      : "Add dimension overlay on image 2 — comps often skip this",
    "Packed for transit; message within 24h if damaged",
  ];
  const descriptionText = [
    title,
    "",
    "Why this listing should convert:",
    ...bullets.map((b) => `• ${b}`),
    "",
    keywords?.length ? `Search language buyers already use: ${keywords.slice(0, 10).join(", ")}` : "",
    price != null ? `Research price band near $${Number(price).toFixed(2)} — verify sold comps before go-live.` : "",
    excerptCue.length
      ? "Competitor copy patterns (do not plagiarize; rewrite): " + excerptCue[0].slice(0, 180)
      : "",
    "Wholesale fulfillment — original photos only. Do not steal competitor images.",
  ]
    .filter(Boolean)
    .join("\n");

  const descriptionHtml = [
    `<h2>${esc(title)}</h2>`,
    `<p>${esc(bullets[0])}</p>`,
    "<ul>",
    ...bullets.slice(1).map((b) => `<li>${esc(b)}</li>`),
    "</ul>",
    `<p><strong>Original photos required.</strong> Competitor URLs are research references only.</p>`,
  ].join("\n");

  return { bullets, descriptionText, descriptionHtml };
}

function esc(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

/**
 * Build ranked listing packages ready to test / promote.
 */
export function buildListingPackages({
  products = [],
  variants = [],
  ideas = [],
  cost = 18,
  maxPackages = 25,
  jobId = "",
} = {}) {
  const competitorTitles = products.map((p) => p.title).filter(Boolean);
  const competitorCommon = mostCommonSpecifics(products);
  const imageStats = competitorImageStats(products);
  const excerpts = products.map((p) => p.descriptionExcerpt).filter(Boolean);

  const clusterSource = [
    ...variants.map((v) => ({ ...v, title: v.title })),
    ...ideas.map((i) => ({ ...i, title: i.title, heatScore: i.heatScore })),
  ];
  const clusters = clusterKeywords(clusterSource, { maxClusters: 20, minSize: 1 });

  const seeds = [];
  const seen = new Set();
  const pushSeed = (row, kind) => {
    const title = String(row.title || "").trim().slice(0, 80);
    if (!title) return;
    const key = title.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    seeds.push({ ...row, title, kind });
  };

  for (const v of variants.filter((v) => v.decision === "TEST_NOW" || v.testPriority === "A")) {
    pushSeed(v, "title_test");
  }
  for (const idea of ideas.slice(0, 40)) pushSeed(idea, "trend_idea");
  for (const v of variants.filter((v) => v.testPriority === "B").slice(0, 10)) {
    pushSeed(v, "title_b");
  }

  const beatPool = products.filter((p) => p.url && !p.scammy);
  const packages = [];

  for (const seed of seeds) {
    if (packages.length >= maxPackages) break;
    const catId = seed.categoryId || beatPool[0]?.categoryId || "25339";
    const beat =
      beatPool.find((p) => String(p.categoryId) === String(catId) && p.image) ||
      beatPool.find((p) => p.image) ||
      beatPool[0] ||
      null;
    const price = Number(seed.suggestedPrice || beat?.price || 59.99);
    const econ = netProfitPerSale({ salePrice: price, productCost: Number(cost) || 18 });
    const kw = extractKeywordsFromTitle(seed.title, null);
    const seo = scoreTitleSeo(seed.title, {
      topUnigrams: kw.secondaryKeywords.map((t) => ({ term: t, share: 0.1 })),
    });
    const ideaFit = scoreIdea(seed, {
      competitorTitles,
      heatScore: seed.heatScore || seed.seoScore || 50,
    });
    const signals = extractContentSignals(
      seed.title,
      `${seed.title} ${beat?.descriptionExcerpt || ""}`,
      beat?.itemSpecifics || competitorCommon
    );
    const material =
      competitorCommon.Material ||
      (/\boak\b/i.test(seed.title) ? "Oak" : /\bbamboo\b/i.test(seed.title) ? "Bamboo" : "Wood");
    const copy = conversionCopy({
      title: seed.title,
      keywords: kw.secondaryKeywords,
      material,
      price,
      competitorExcerpts: excerpts,
      signals,
    });
    const imagePlan = imageSeoChecklist({ title: seed.title, primaryKeyword: kw.primaryKeyword });
    imagePlan.competitorStats = imageStats;
    imagePlan.mustBeatImageCount = imageStats.beatWith;
    const cluster = clusters.clusters.find((c) =>
      (c.sampleTitles || []).some((t) => t.includes(seed.title.toLowerCase().slice(0, 24)))
    );

    const draft = draftListing({
      title: seed.title,
      salePrice: price,
      url: beat?.url,
      condition: "NEW",
    });
    draft.itemSpecifics = mergeSpecifics(draft.itemSpecifics, competitorCommon, seed.title);
    draft.bullets = copy.bullets;
    draft.descriptionHtml = copy.descriptionHtml;
    draft.descriptionText = copy.descriptionText;

    packages.push({
      packageId: `LP-${packages.length + 1}`,
      jobId,
      kind: seed.kind,
      title: seed.title.slice(0, 80),
      categoryId: catId,
      categoryPath: seed.categoryPath || seed.categoryLabel || beat?.categoryPath,
      salePrice: price,
      productCost: Number(cost) || 18,
      estFees: econ.fees,
      estNet: econ.net,
      estMarginPct: econ.marginPct,
      seoScore: seed.seoScore ?? Math.round((seo.seoScore || 0) * 100),
      ideaScore: ideaFit.ideaScore,
      uniqueness: ideaFit.uniqueness,
      decision: ideaFit.decision,
      clusterId: cluster?.clusterId || null,
      clusterSeed: cluster?.seed || null,
      testPlan: cluster?.testPlan || { listingsToTest: 1 },
      keywords: kw,
      itemSpecifics: draft.itemSpecifics,
      bullets: copy.bullets,
      descriptionText: copy.descriptionText,
      descriptionHtml: copy.descriptionHtml,
      imagePlan: {
        beatWith: imageStats.beatWith,
        competitorAvg: imageStats.avgImageCount,
        gap: imageStats.gap,
        shots: imagePlan.recommendations,
        note: "Original photos only — competitor image URLs are research, not assets",
      },
      beatThis: beat
        ? {
            title: beat.title,
            price: beat.price,
            url: beat.url,
            image: beat.image,
            imageCount: beat.imageCount,
            weaknesses:
              (beat.imageCount || 0) < 6
                ? "Thin gallery"
                : (beat.descriptionLength || 0) < 200
                  ? "Thin description"
                  : "Differentiate on material + lifestyle hero",
          }
        : null,
      outrank: [
        `Front-load ${kw.primaryKeyword || "material + use-case"} in title`,
        `Ship ${imageStats.beatWith}+ original images (comps avg ${imageStats.avgImageCount})`,
        "Item specifics completeness vs comps",
        "Benefit-first description; no qty-spam",
      ],
      draft,
      sourceUrl: beat?.url || null,
    });
  }

  packages.sort((a, b) => (b.ideaScore || 0) - (a.ideaScore || 0) || (b.seoScore || 0) - (a.seoScore || 0));
  return {
    packageCount: packages.length,
    clusters,
    imageStats,
    competitorSpecifics: competitorCommon,
    packages: packages.slice(0, maxPackages),
  };
}

export function packagesToCsv(packages = []) {
  const cols = [
    "packageId",
    "decision",
    "title",
    "salePrice",
    "productCost",
    "estNet",
    "seoScore",
    "ideaScore",
    "categoryId",
    "clusterSeed",
    "beatUrl",
    "imageBeatWith",
    "primaryKeyword",
    "outrank",
  ];
  const esc = (v) => {
    const s = Array.isArray(v) ? v.join(" | ") : String(v ?? "");
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [cols.join(",")];
  for (const p of packages) {
    lines.push(
      [
        p.packageId,
        p.decision,
        p.title,
        p.salePrice,
        p.productCost,
        p.estNet,
        p.seoScore,
        p.ideaScore,
        p.categoryId,
        p.clusterSeed,
        p.beatThis?.url,
        p.imagePlan?.beatWith,
        p.keywords?.primaryKeyword,
        p.outrank,
      ]
        .map(esc)
        .join(",")
    );
  }
  return lines.join("\n") + "\n";
}
