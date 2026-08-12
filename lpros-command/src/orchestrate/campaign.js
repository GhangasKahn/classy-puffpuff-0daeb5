/**
 * Marathon campaign — 4–5 categories, 100s of products/ideas/variants, trend rollup.
 * Always intended for long async local runs (:8790 / CLI). Netlify should refuse or dry-run.
 */
import crypto from "node:crypto";
import { EventEmitter } from "node:events";
import path from "node:path";
import fs from "node:fs";
import os from "node:os";

import { loadEbayEnv } from "../../../lpros/src/agents/_env.js";
import { productsToCsv } from "../../../lpros/src/core/listing_content.js";
import { buildCampaignTrends, trendsToCsv } from "../../../lpros/src/core/trends.js";
import { researchCategoryLane, researchCategoryLaneDry } from "./lane.js";

const DATA_DIR = process.env.LPROS_ORCH_DIR || path.join(os.tmpdir(), "lpros-orch");

function ensureDir(d) {
  if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
}
ensureDir(DATA_DIR);

/** @type {Map<string, object>} */
const jobs = new Map();
export const campaignBus = new EventEmitter();
campaignBus.setMaxListeners(50);

function id() {
  return `camp_${Date.now().toString(36)}_${crypto.randomBytes(3).toString("hex")}`;
}

function persist(job) {
  try {
    fs.writeFileSync(path.join(DATA_DIR, `${job.id}.json`), JSON.stringify(job, null, 2));
  } catch {
    /* ignore */
  }
}

function appendEvent(job, level, message, data = {}) {
  const ev = { at: new Date().toISOString(), level, message, ...data };
  job.events.push(ev);
  if (job.events.length > 4000) job.events.splice(0, job.events.length - 4000);
  campaignBus.emit("event", { jobId: job.id, event: ev });
  persist(job);
  return ev;
}

export function getCampaignJob(jobId) {
  if (jobs.has(jobId)) return jobs.get(jobId);
  const p = path.join(DATA_DIR, `${jobId}.json`);
  if (fs.existsSync(p)) {
    const job = JSON.parse(fs.readFileSync(p, "utf8"));
    jobs.set(jobId, job);
    return job;
  }
  return null;
}

/** Default 5-lane Home/Office organization campaign */
export const DEFAULT_MARATHON_CATEGORIES = [
  {
    categoryId: "25339",
    label: "Desk & drawer organizers",
    queries: [
      "solid wood desk organizer",
      "bamboo desk organizer",
      "oak pen tray",
      "walnut desk tray",
    ],
  },
  {
    categoryId: "20625",
    label: "Home storage",
    queries: ["wood drawer organizer", "bamboo closet organizer", "solid wood storage tray"],
  },
  {
    categoryId: "20601",
    label: "Household organization",
    queries: ["desktop mail organizer", "letter tray wood", "file organizer desktop"],
  },
  {
    categoryId: "116711",
    label: "Kitchen storage",
    queries: ["bamboo utensil organizer", "wood spice rack", "kitchen drawer organizer wood"],
  },
  {
    categoryId: "36027",
    label: "Bathroom storage",
    queries: ["bamboo bath tray", "wood vanity organizer", "shower caddy wood"],
  },
];

function normalizeCategories(input, fallbackQuery) {
  if (Array.isArray(input) && input.length) {
    return input
      .map((c) => {
        if (typeof c === "string" || typeof c === "number") {
          return {
            categoryId: String(c),
            label: String(c),
            queries: fallbackQuery ? [fallbackQuery] : ["organizer"],
          };
        }
        return {
          categoryId: String(c.categoryId || c.id || ""),
          label: c.label || c.category || String(c.categoryId || c.id || "lane"),
          queries: (c.queries || c.seedQueries || (c.query ? [c.query] : [])).filter(Boolean),
        };
      })
      .filter((c) => c.categoryId)
      .slice(0, 8);
  }
  return DEFAULT_MARATHON_CATEGORIES.map((c) => ({
    ...c,
    queries: fallbackQuery ? [fallbackQuery, ...c.queries] : c.queries,
  }));
}

function slimProduct(p) {
  return {
    itemId: p.itemId,
    title: p.title,
    price: p.price,
    url: p.url,
    image: p.image,
    images: (p.images || []).slice(0, 6),
    imageCount: p.imageCount,
    seller: p.seller,
    categoryPath: p.categoryPath,
    categoryId: p.categoryId,
    contentSignals: p.contentSignals,
    perceivedValue: p.perceivedValue,
    detailFetched: p.detailFetched,
    rank: p.rank,
    specificsSummary: p.specificsSummary,
    descriptionExcerpt: (p.descriptionExcerpt || "").slice(0, 240),
  };
}

function joinCampaignWorkbook({ productCsv, titleCsv, trendsCsv, ideasCsv }) {
  return [
    "# SHEET: PRODUCT_RESEARCH",
    productCsv.trimEnd(),
    "",
    "# SHEET: TITLE_KEYWORD_TESTS",
    titleCsv.trimEnd(),
    "",
    "# SHEET: TRENDS",
    trendsCsv.trimEnd(),
    "",
    "# SHEET: IDEAS",
    ideasCsv.trimEnd(),
    "",
  ].join("\n");
}

function ideasToCsv(ideas) {
  const cols = ["rank", "title", "family", "categoryId", "categoryLabel", "heatScore", "drivers", "rationale"];
  const esc = (v) => {
    const s = Array.isArray(v) ? v.join("|") : String(v ?? "");
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return (
    [cols.join(",")]
      .concat(
        ideas.map((idea, i) =>
          [
            i + 1,
            idea.title,
            idea.family,
            idea.categoryId,
            idea.categoryLabel,
            idea.heatScore,
            idea.drivers,
            idea.rationale,
          ]
            .map(esc)
            .join(",")
        )
      )
      .join("\n") + "\n"
  );
}

export async function runCampaign(job) {
  const cfg = job.config;
  await loadEbayEnv();
  job.status = "running";
  job.updatedAt = new Date().toISOString();
  const cats = cfg.categories;
  appendEvent(
    job,
    "info",
    `Marathon campaign start — ${cats.length} categories · target ~${cfg.variantCount} variants/lane · ${cfg.detailCount} details/lane · ${cfg.ideasTarget} ideas`,
    { phase: "deploy" }
  );
  job.progress = { phase: "lanes", pct: 2, lane: 0, laneTotal: cats.length };

  const laneResults = [];
  const allProducts = [];
  const allVariants = [];
  const titleCsvParts = [];

  for (let i = 0; i < cats.length; i++) {
    const lane = cats[i];
    const pctBase = Math.round((i / cats.length) * 85) + 5;
    job.progress = {
      phase: "lane",
      pct: pctBase,
      lane: i + 1,
      laneTotal: cats.length,
      categoryId: lane.categoryId,
      label: lane.label,
    };
    appendEvent(job, "info", `Lane ${i + 1}/${cats.length}: ${lane.label} (${lane.categoryId})`, {
      phase: "lane",
    });
    persist(job);

    const log = (level, message, data) => appendEvent(job, level, message, data);
    let result;
    try {
      result = cfg.dryRun
        ? researchCategoryLaneDry(lane, {
            jobId: job.id,
            cost: cfg.cost,
            suggestedPrice: cfg.suggestedPrice,
            variantCount: cfg.variantCount,
            defaultQuery: cfg.query,
          })
        : await researchCategoryLane(lane, {
            jobId: job.id,
            cost: cfg.cost,
            minPrice: cfg.minPrice,
            maxPrice: cfg.maxPrice,
            suggestedPrice: cfg.suggestedPrice,
            intelLimit: cfg.intelLimit,
            crawlPages: cfg.crawlPages,
            crawlLimit: cfg.crawlLimit,
            detailCount: cfg.detailCount,
            detailDelayMs: cfg.detailDelayMs,
            variantCount: cfg.variantCount,
            liveProbeCount: cfg.liveProbeCount,
            sheetRows: cfg.sheetRows,
            probeDelayMs: cfg.probeDelayMs,
            maxQueriesPerCategory: cfg.maxQueriesPerCategory,
            boardCap: cfg.boardCap,
            defaultQuery: cfg.query,
            log,
          });
    } catch (e) {
      appendEvent(job, "error", `Lane ${lane.label} failed: ${e.message}`, { phase: "lane" });
      job.laneErrors = job.laneErrors || [];
      job.laneErrors.push({ categoryId: lane.categoryId, error: e.message });
      continue;
    }

    laneResults.push(result);
    allProducts.push(...result.products.map((p) => ({ ...p, categoryId: result.categoryId, categoryPath: result.label })));
    allVariants.push(...result.variants);
    titleCsvParts.push(result.spreadsheetCsv);
    job.checkpoints = job.checkpoints || [];
    job.checkpoints.push({
      at: new Date().toISOString(),
      categoryId: result.categoryId,
      label: result.label,
      products: result.products.length,
      variants: result.variants.length,
      heat: result.snapshot?.heatScore,
    });
    // Checkpoint persist after each lane (long-run safety)
    job.partial = {
      productCount: allProducts.length,
      variantCount: allVariants.length,
      lanesDone: laneResults.length,
    };
    persist(job);
  }

  if (!laneResults.length) {
    throw new Error("Marathon produced zero successful category lanes");
  }

  job.progress = { phase: "trends", pct: 90 };
  appendEvent(job, "info", "Building cross-category trend analysis + idea factory", { phase: "trends" });

  const trends = buildCampaignTrends({
    lanes: laneResults.map((l) => ({
      categoryId: l.categoryId,
      label: l.label,
      snapshot: l.snapshot,
      momentum: l.momentum,
      titles: l.titles,
    })),
    ideasTarget: cfg.ideasTarget || 250,
  });

  // Dedupe products by itemId/url
  const seen = new Set();
  const dedupedProducts = [];
  for (const p of allProducts) {
    const key = p.itemId || p.url || p.title;
    if (seen.has(key)) continue;
    seen.add(key);
    dedupedProducts.push(p);
  }

  // Dedupe variants by title
  const seenT = new Set();
  const dedupedVariants = [];
  for (const v of allVariants) {
    const key = String(v.title || "").toLowerCase();
    if (!key || seenT.has(key)) continue;
    seenT.add(key);
    dedupedVariants.push(v);
  }
  dedupedVariants.sort((a, b) => (b.seoScore || 0) - (a.seoScore || 0));

  const productCsv = productsToCsv(dedupedProducts);
  const titleBody = dedupedVariants
    .slice(0, cfg.sheetRowsTotal || 800)
    .map((r, i) => {
      // reuse existing decision fields if present
      const cols = [
        i + 1,
        r.testPriority,
        r.decision,
        r.title,
        r.seoScore,
        r.primaryKeyword,
        (r.secondaryKeywords || []).join(" | "),
        r.categoryId,
        r.categoryPath,
        r.suggestedPrice,
        r.landedCost,
        r.estFees,
        r.estNet,
        r.estMarginPct,
        r.competitionProxy,
        r.liveTotal,
        r.liveMedianPrice,
        r.liveImageCoverage,
      ];
      return cols
        .map((v) => {
          const s = v == null ? "" : String(v);
          return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
        })
        .join(",");
    })
    .join("\n");
  const titleCsvClean =
    "rank,test_priority,decision,title,seo_score,primary_keyword,secondary_keywords,category_id,category_path,suggested_price,landed_cost,est_fees,est_net,est_margin_pct,competition_proxy,live_total,live_median_price,live_image_coverage\n" +
    titleBody +
    "\n";

  const trendsCsv = trendsToCsv(trends);
  const ideasCsv = ideasToCsv(trends.ideas || []);
  const workbookCsv = joinCampaignWorkbook({
    productCsv,
    titleCsv: titleCsvClean,
    trendsCsv,
    ideasCsv,
  });

  job.results = {
    mode: "marathon",
    researched: true,
    categoryCount: laneResults.length,
    productCount: dedupedProducts.length,
    productsWithImages: dedupedProducts.filter((p) => p.image).length,
    productsWithUrls: dedupedProducts.filter((p) => p.url).length,
    productsWithDetail: dedupedProducts.filter((p) => p.detailFetched).length,
    variantTotalGenerated: dedupedVariants.length,
    ideaCount: trends.ideaCount,
    products: dedupedProducts.map(slimProduct),
    variants: dedupedVariants.slice(0, cfg.sheetRowsTotal || 800),
    gallery: dedupedProducts
      .filter((p) => p.image)
      .slice(0, 48)
      .map((p) => ({
        itemId: p.itemId,
        title: p.title,
        image: p.image,
        price: p.price,
        url: p.url,
        categoryPath: p.categoryPath,
        imageCount: p.imageCount,
      })),
    lanes: laneResults.map((l) => ({
      categoryId: l.categoryId,
      label: l.label,
      queries: l.queries,
      productCount: l.products.length,
      variantCount: l.variants.length,
      heatScore: l.snapshot?.heatScore,
      snapshot: l.snapshot,
      risingKeywords: l.momentum?.rising?.slice(0, 10),
      market: l.intel?.market
        ? {
            activeTotal: l.intel.market.activeTotal,
            sampleSize: l.intel.market.sampleSize,
            priceLadder: l.intel.market.priceLadder,
            density: l.intel.market.density,
          }
        : null,
    })),
    trends: {
      caveat: trends.caveat,
      categoryHeat: trends.categoryHeat,
      hottestCategory: trends.hottestCategory,
      risingKeywords: trends.risingKeywords?.slice(0, 30),
      materialDemand: trends.materialDemand,
      benefitDemand: trends.benefitDemand,
      ideaCount: trends.ideaCount,
      ideasPreview: (trends.ideas || []).slice(0, 40),
    },
    productSpreadsheetCsv: productCsv,
    spreadsheetCsv: titleCsvClean,
    trendsCsv,
    ideasCsv,
    workbookCsv,
    recommendations: {
      hottestLanes: (trends.categoryHeat || []).slice(0, 3),
      risingKeywords: (trends.risingKeywords || []).slice(0, 15),
      productsToBeat: dedupedProducts
        .filter((p) => p.image && !p.scammy)
        .slice(0, 20)
        .map((p) => ({
          title: p.title,
          price: p.price,
          url: p.url,
          image: p.image,
          categoryPath: p.categoryPath,
          imageCount: p.imageCount,
        })),
      testNow: dedupedVariants.filter((r) => r.decision === "TEST_NOW").slice(0, 25),
      topIdeas: (trends.ideas || []).slice(0, 30),
    },
  };

  job.progress = { phase: "done", pct: 100, lane: cats.length, laneTotal: cats.length };
  job.status = "completed";
  job.updatedAt = new Date().toISOString();
  appendEvent(
    job,
    "info",
    `Marathon complete — ${laneResults.length} lanes · ${dedupedProducts.length} products · ${dedupedVariants.length} variants · ${trends.ideaCount} ideas`,
    { phase: "done" }
  );
  persist(job);
  campaignBus.emit("complete", { jobId: job.id });
  return job;
}

export function deployCampaign(config = {}, { sync = false } = {}) {
  const categories = normalizeCategories(config.categories, config.query || config.q);
  const marathon = config.mode === "marathon" || config.marathon === true || categories.length > 1;

  const job = {
    id: id(),
    type: "campaign",
    status: "queued",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    config: {
      mode: marathon ? "marathon" : "multi",
      query: String(config.query || config.q || "").trim() || categories[0]?.queries?.[0] || "",
      categories,
      cost: config.cost != null ? Number(config.cost) : 18,
      minPrice: config.minPrice != null ? Number(config.minPrice) : 35,
      maxPrice: config.maxPrice != null ? Number(config.maxPrice) : 200,
      suggestedPrice: config.suggestedPrice != null ? Number(config.suggestedPrice) : undefined,
      // Marathon scale defaults
      variantCount: config.variantCount != null ? Number(config.variantCount) : 250,
      liveProbeCount: config.liveProbeCount != null ? Number(config.liveProbeCount) : 10,
      sheetRows: config.sheetRows != null ? Number(config.sheetRows) : 120,
      sheetRowsTotal: config.sheetRowsTotal != null ? Number(config.sheetRowsTotal) : 800,
      intelLimit: config.intelLimit != null ? Number(config.intelLimit) : 120,
      crawlPages: config.crawlPages != null ? Number(config.crawlPages) : 4,
      crawlLimit: config.crawlLimit != null ? Number(config.crawlLimit) : 600,
      detailCount: config.detailCount != null ? Number(config.detailCount) : 30,
      detailDelayMs: config.detailDelayMs || 200,
      probeDelayMs: config.probeDelayMs || 300,
      maxQueriesPerCategory: config.maxQueriesPerCategory || 5,
      boardCap: config.boardCap || 150,
      ideasTarget: config.ideasTarget != null ? Number(config.ideasTarget) : 250,
      dryRun: Boolean(config.dryRun),
    },
    progress: { phase: "queued", pct: 0 },
    events: [],
    results: null,
    error: null,
    checkpoints: [],
  };

  if (!job.config.categories.length) {
    job.status = "failed";
    job.error = "categories required";
    jobs.set(job.id, job);
    persist(job);
    return job;
  }

  jobs.set(job.id, job);
  appendEvent(job, "info", `Campaign queued (${job.config.categories.length} categories)`, {
    phase: "queued",
  });

  const run = async () => {
    try {
      await runCampaign(job);
    } catch (e) {
      job.status = "failed";
      job.error = e.message || String(e);
      job.updatedAt = new Date().toISOString();
      appendEvent(job, "error", `Campaign failed: ${job.error}`, { phase: "error" });
      persist(job);
      campaignBus.emit("failed", { jobId: job.id, error: job.error });
    }
  };

  if (sync) return run().then(() => job);
  setImmediate(() => run());
  return job;
}

export function getCampaignEvents(jobId, afterIndex = 0) {
  const job = getCampaignJob(jobId);
  if (!job) return null;
  return {
    jobId,
    status: job.status,
    progress: job.progress,
    events: job.events.slice(afterIndex),
    nextIndex: job.events.length,
    partial: job.partial || null,
    checkpoints: job.checkpoints || [],
  };
}

export function getCampaignSpreadsheet(jobId, { workbook = true, products = false, trends = false, ideas = false } = {}) {
  const job = getCampaignJob(jobId);
  if (!job) return null;
  if (!job.results) return { jobId, ready: false, status: job.status };
  let csv = job.results.workbookCsv;
  if (products) csv = job.results.productSpreadsheetCsv;
  else if (trends) csv = job.results.trendsCsv;
  else if (ideas) csv = job.results.ideasCsv;
  else if (!workbook) csv = job.results.spreadsheetCsv;
  return {
    jobId,
    ready: true,
    status: job.status,
    csv,
    results: job.results,
  };
}

/** Merge campaign jobs into listJobs-compatible rows */
export function listCampaignJobs(limit = 40) {
  const files = fs.existsSync(DATA_DIR)
    ? fs.readdirSync(DATA_DIR).filter((f) => f.startsWith("camp_") && f.endsWith(".json"))
    : [];
  for (const f of files) {
    const jid = f.replace(/\.json$/, "");
    if (!jobs.has(jid)) {
      try {
        jobs.set(jid, JSON.parse(fs.readFileSync(path.join(DATA_DIR, f), "utf8")));
      } catch {
        /* skip */
      }
    }
  }
  return [...jobs.values()]
    .filter((j) => j.type === "campaign" || String(j.id).startsWith("camp_"))
    .sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)))
    .slice(0, limit)
    .map((j) => ({
      id: j.id,
      type: "campaign",
      status: j.status,
      createdAt: j.createdAt,
      updatedAt: j.updatedAt,
      query: j.config?.query,
      categoryCount: j.config?.categories?.length,
      progress: j.progress,
      productCount: j.results?.productCount || j.partial?.productCount || 0,
      variantCount: j.results?.variantTotalGenerated || j.partial?.variantCount || 0,
      ideaCount: j.results?.ideaCount || 0,
      error: j.error || null,
    }));
}
