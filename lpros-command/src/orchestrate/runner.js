/**
 * Hardened agent orchestration — real Browse intel + item detail + product board.
 * Official eBay Browse APIs only (getItem for listing page content — not HTML scrape).
 */
import crypto from "node:crypto";
import { EventEmitter } from "node:events";
import path from "node:path";
import fs from "node:fs";
import os from "node:os";

import { crawlCategory } from "../../../lpros/src/agents/crawl.js";
import { runResearchPipeline } from "../../../lpros/src/pipeline.js";
import { competitorIntel } from "../intel/competitor.js";
import {
  mineKeywordPatterns,
  generateTitleVariations,
  scoreTitleSeo,
  imageSeoChecklist,
  buildConversionDescription,
  extractKeywordsFromTitle,
} from "../../../lpros/src/core/seo.js";
import { toDecisionCsv } from "../../../lpros/src/core/spreadsheet.js";
import {
  toProductResearchRow,
  productsToCsv,
  extractContentSignals,
} from "../../../lpros/src/core/listing_content.js";
import { netProfitPerSale } from "../../../lpros/src/core/economics.js";
import {
  searchActiveListings,
  enrichItemsWithDetails,
} from "../../../ebay-sold-items/src/ebay/browse.js";
import { loadEbayEnv } from "../../../lpros/src/agents/_env.js";

const DATA_DIR = process.env.LPROS_ORCH_DIR || path.join(os.tmpdir(), "lpros-orch");

function ensureDir(d) {
  if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
}
ensureDir(DATA_DIR);

/** @type {Map<string, object>} */
const jobs = new Map();
const bus = new EventEmitter();
bus.setMaxListeners(50);

function id() {
  return `job_${Date.now().toString(36)}_${crypto.randomBytes(3).toString("hex")}`;
}

function persist(job) {
  try {
    // Strip huge HTML from persisted events/results already truncated
    fs.writeFileSync(path.join(DATA_DIR, `${job.id}.json`), JSON.stringify(job, null, 2));
  } catch {
    /* ignore */
  }
}

function appendEvent(job, level, message, data = {}) {
  const ev = { at: new Date().toISOString(), level, message, ...data };
  job.events.push(ev);
  if (job.events.length > 2000) job.events.splice(0, job.events.length - 2000);
  bus.emit("event", { jobId: job.id, event: ev });
  persist(job);
  return ev;
}

export function getJob(jobId) {
  if (jobs.has(jobId)) return jobs.get(jobId);
  const p = path.join(DATA_DIR, `${jobId}.json`);
  if (fs.existsSync(p)) {
    const job = JSON.parse(fs.readFileSync(p, "utf8"));
    jobs.set(jobId, job);
    return job;
  }
  return null;
}

export function listJobs(limit = 40) {
  const files = fs.existsSync(DATA_DIR) ? fs.readdirSync(DATA_DIR).filter((f) => f.endsWith(".json")) : [];
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
    .sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)))
    .slice(0, limit)
    .map((j) => ({
      id: j.id,
      status: j.status,
      createdAt: j.createdAt,
      updatedAt: j.updatedAt,
      query: j.config?.query,
      categoryId: j.config?.categoryId,
      progress: j.progress,
      productCount: j.results?.products?.length || 0,
      variantCount: j.results?.variants?.length || 0,
      error: j.error || null,
    }));
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function probeTitleLive(title, categoryId, limit = 20) {
  try {
    const res = await searchActiveListings({
      q: title.slice(0, 80),
      categoryIds: categoryId || undefined,
      limit,
      sort: "bestMatch",
    });
    const items = res.items || [];
    const prices = items
      .map((it) => Number(it.price))
      .filter((n) => Number.isFinite(n))
      .sort((a, b) => a - b);
    const withImg = items.filter((it) => it.image || (it.images || []).length).length;
    const mid = prices.length ? prices[Math.floor(prices.length / 2)] : null;
    return {
      liveTotal: res.total ?? items.length,
      liveMedianPrice: mid,
      liveImageCoverage: items.length ? withImg / items.length : null,
      competitionProxy: Math.min(100, Math.round(((res.total || items.length) / 100) * 2)),
    };
  } catch (e) {
    return { liveError: e.message, liveTotal: null, competitionProxy: null };
  }
}

function slimProduct(p) {
  return {
    itemId: p.itemId,
    title: p.title,
    price: p.price,
    url: p.url,
    image: p.image,
    images: (p.images || []).slice(0, 8),
    imageCount: p.imageCount,
    imageSeoScore: p.imageSeoScore,
    seller: p.seller,
    condition: p.condition,
    brand: p.brand,
    categoryPath: p.categoryPath,
    specificsSummary: p.specificsSummary,
    descriptionExcerpt: p.descriptionExcerpt,
    contentSignals: p.contentSignals,
    perceivedValue: p.perceivedValue,
    scammy: p.scammy,
    rank: p.rank,
    rankScore: p.rankScore,
    sellThrough: p.sellThrough,
    ctrProxy: p.ctrProxy,
    popularity: p.popularity,
    detailFetched: p.detailFetched,
  };
}

/** Offline fixture only — never the default path. */
async function runDryMission(job) {
  const cfg = job.config;
  appendEvent(job, "warn", "Dry-run: synthetic products only (tests). Live deploy uses real Browse intel.", {
    phase: "crawl",
  });
  const seedTitles = [
    `Solid wood ${cfg.query} oak desktop storage`,
    `Bamboo ${cfg.query} clutter solution home office`,
    `Walnut desk organizer multi-tier upgrade`,
  ];
  const patterns = mineKeywordPatterns(seedTitles);
  const products = seedTitles.map((title, i) =>
    toProductResearchRow(
      {
        id: `dry_${i}`,
        title,
        price: 49 + i * 5,
        url: `https://www.ebay.com/itm/dry${i}`,
        image: null,
        images: [],
        seller: "dry_seller",
        descriptionText: `${title}. Solid wood. Desk clutter solution. Dimensions in listing.`,
        itemSpecifics: { Material: "Wood", Brand: "Unbranded" },
        rank: i + 1,
        detailFetched: false,
      },
      { jobId: job.id, query: cfg.query, categoryId: cfg.categoryId }
    )
  );
  const rawVariants = generateTitleVariations({
    seed: cfg.query,
    maxTitles: Math.min(cfg.variantCount || 40, 80),
    patterns,
  });
  const cost = Number(cfg.cost) || 18;
  const priceHint = Number(cfg.suggestedPrice) || 59.99;
  const scored = scoreVariants(rawVariants, patterns, { cost, priceHint, cfg, job });
  const sheet = toDecisionCsv(scored.slice(0, 40), {
    jobId: job.id,
    query: cfg.query,
    categoryId: cfg.categoryId,
    landedCost: cost,
    suggestedPrice: priceHint,
  });
  job.results = buildResults({
    job,
    products,
    intel: { market: { activeTotal: 3, sampleSize: 3 }, dryRun: true },
    patterns,
    narrowedCategory: { categoryId: cfg.categoryId, categoryPath: cfg.category || "Home" },
    scored,
    sheet,
    pipeline: null,
  });
  job.progress = { phase: "done", pct: 100 };
  job.status = "completed";
  job.updatedAt = new Date().toISOString();
  appendEvent(job, "info", `Dry mission complete — ${products.length} products, ${sheet.rows.length} title rows`, {
    phase: "done",
  });
  persist(job);
  bus.emit("complete", { jobId: job.id });
  return job;
}

function scoreVariants(rawVariants, patterns, { cost, priceHint, cfg }) {
  return rawVariants
    .filter((v) => !v.scammy)
    .map((v) => {
      const seo = scoreTitleSeo(v.title, patterns, { salePrice: priceHint });
      const kw = extractKeywordsFromTitle(v.title, patterns);
      const econ = netProfitPerSale({ salePrice: priceHint, productCost: cost });
      const imageSeo = imageSeoChecklist({ title: v.title, primaryKeyword: kw.primaryKeyword });
      const description = buildConversionDescription({
        title: v.title,
        keywords: kw.secondaryKeywords,
        material: (patterns.materialDemand || [])[0]?.term,
        price: priceHint,
      });
      const seoPct = Math.round((seo.seoScore || 0) * 100);
      return {
        ...v,
        seoScore: seoPct,
        primaryKeyword: kw.primaryKeyword,
        secondaryKeywords: kw.secondaryKeywords,
        outrankAdvice: seo.outrankAdvice,
        suggestedPrice: priceHint,
        landedCost: cost,
        estFees: econ.fees,
        estNet: econ.net,
        estMarginPct: econ.marginPct,
        imageSeo,
        description,
        competitionProxy: null,
        liveTotal: null,
        liveMedianPrice: null,
        liveImageCoverage: null,
        variantFamily: v.family || "base",
        testPriority: seoPct >= 70 ? "A" : seoPct >= 55 ? "B" : "C",
        categoryId: cfg.categoryId,
        categoryPath: cfg.category,
      };
    })
    .sort((a, b) => (b.seoScore || 0) - (a.seoScore || 0));
}

function buildResults({
  job,
  products,
  intel,
  patterns,
  narrowedCategory,
  scored,
  sheet,
  pipeline,
}) {
  const productCsv = productsToCsv(products);
  return {
    researched: true,
    productCount: products.length,
    productsWithImages: products.filter((p) => p.image).length,
    productsWithUrls: products.filter((p) => p.url).length,
    productsWithDetail: products.filter((p) => p.detailFetched).length,
    products: products.map(slimProduct),
    productSpreadsheetCsv: productCsv,
    gallery: products.filter((p) => p.image).slice(0, 24).map((p) => ({
      itemId: p.itemId,
      title: p.title,
      image: p.image,
      images: p.images,
      price: p.price,
      url: p.url,
      rank: p.rank,
      seller: p.seller,
      imageCount: p.imageCount,
      contentSignals: p.contentSignals,
    })),
    intel: {
      market: intel?.market || null,
      vsZik: intel?.vsZik || null,
      activeTotal: intel?.market?.activeTotal ?? null,
      sampleSize: intel?.market?.sampleSize ?? products.length,
      priceLadder: intel?.market?.priceLadder || null,
      topSellers: intel?.market?.topSellers || null,
    },
    narrowedCategory,
    patterns: {
      topKeywords: (patterns.topUnigrams || []).slice(0, 30),
      topBigrams: (patterns.topBigrams || []).slice(0, 20),
      buyerPhrases: patterns.buyerLanguage || [],
      attributeHints: patterns.materialDemand || [],
      contentSignalsRollup: rollupSignals(products),
    },
    pipelineSummary: pipeline
      ? {
          category: pipeline.category,
          queries: pipeline.queries,
          topTitle: pipeline.ranked?.[0]?.title || pipeline.market?.ranked?.[0]?.title,
        }
      : null,
    variants: sheet.rows,
    variantTotalGenerated: scored.length,
    spreadsheetCsv: sheet.csv,
    /** Combined workbook: products first, then title tests */
    workbookCsv: joinWorkbooks(productCsv, sheet.csv),
    columns: sheet.columns,
    recommendations: {
      productsToBeat: products
        .filter((p) => !p.scammy && p.image)
        .slice(0, 10)
        .map((p) => ({
          title: p.title,
          price: p.price,
          url: p.url,
          image: p.image,
          imageCount: p.imageCount,
          weaknesses: productWeaknesses(p),
        })),
      testNow: sheet.rows.filter((r) => r.decision === "TEST_NOW").slice(0, 15),
      rewrite: sheet.rows.filter((r) => r.decision === "REWRITE").slice(0, 10),
      imagePriority: products
        .filter((p) => (p.imageCount || 0) < 6)
        .slice(0, 10)
        .map((p) => ({
          title: p.title,
          url: p.url,
          imageCount: p.imageCount,
          actions: p.imageRecommendations?.slice(0, 4) || ["Add lifestyle + detail gallery"],
        })),
    },
  };
}

function rollupSignals(products) {
  const m = new Map();
  for (const p of products) {
    for (const s of p.contentSignals || []) m.set(s, (m.get(s) || 0) + 1);
  }
  return [...m.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([signal, count]) => ({ signal, count }));
}

function productWeaknesses(p) {
  const w = [];
  if ((p.imageCount || 0) < 6) w.push(`Only ${p.imageCount || 0} images — outrank with 8+ gallery`);
  if (!(p.contentSignals || []).includes("size_trust")) w.push("Weak dimensions language in description");
  if (!(p.contentSignals || []).includes("material_premium")) w.push("Material not emphasized");
  if ((p.descriptionLength || 0) < 200) w.push("Thin description — opportunity for benefit-first copy");
  if (!w.length) w.push("Strong listing — differentiate on price band + hero lifestyle CTR");
  return w;
}

function joinWorkbooks(productCsv, titleCsv) {
  return [
    "# SHEET: PRODUCT_RESEARCH (real Browse listings + getItem page content)",
    productCsv.trimEnd(),
    "",
    "# SHEET: TITLE_KEYWORD_TESTS (outrank variants grounded in mined language)",
    titleCsv.trimEnd(),
    "",
  ].join("\n");
}

/**
 * Core hardened mission — real products required.
 */
export async function runMission(job) {
  const cfg = job.config;
  await loadEbayEnv();
  job.status = "running";
  job.updatedAt = new Date().toISOString();
  appendEvent(job, "info", "Mission deployed — hardened research core starting", { phase: "deploy" });
  job.progress = { phase: "intel", pct: 5 };

  if (cfg.dryRun) return runDryMission(job);

  let crawl = null;
  let pipeline = null;
  let intel = null;

  // ── Phase 1: Competitor INTEL (primary — real listings) ──
  appendEvent(job, "info", `Intel: searching live Browse market for "${cfg.query}"`, {
    phase: "intel",
    categoryId: cfg.categoryId,
  });
  try {
    const cost = Number(cfg.cost) || 18;
    const midPrice = ((cfg.minPrice || 35) + (cfg.maxPrice || 200)) / 2;
    intel = await competitorIntel({
      q: cfg.query,
      categoryId: cfg.categoryId,
      minPrice: cfg.minPrice || 35,
      maxPrice: cfg.maxPrice || 200,
      limit: cfg.intelLimit || 100,
      productCostRatio: Math.min(0.85, cost / Math.max(midPrice, 1)),
    });
    const n = intel?.lethalCandidates?.length || 0;
    const withImg = (intel?.lethalCandidates || []).filter((c) => c.image).length;
    appendEvent(
      job,
      "info",
      `Intel ready — market total ${intel?.market?.activeTotal ?? "?"} · sample ${intel?.market?.sampleSize ?? 0} · board ${n} · images ${withImg}`,
      { phase: "intel" }
    );
    job.progress = { phase: "intel", pct: 20 };
  } catch (e) {
    appendEvent(job, "error", `Intel failed: ${e.message}`, { phase: "intel" });
    throw new Error(`Hardened core requires live intel — ${e.message}`);
  }

  if (!(intel?.lethalCandidates?.length || intel?.market?.sampleSize)) {
    throw new Error("Zero products from Browse intel — check query/category/credentials");
  }

  // ── Phase 2: Category crawl (more real titles + density) ──
  try {
    appendEvent(job, "info", "Crawl: paginating category via Browse API (not HTML scrape)", {
      phase: "crawl",
    });
    crawl = await crawlCategory({
      categoryId: cfg.categoryId,
      q: cfg.query,
      minPrice: cfg.minPrice || 35,
      maxPrice: cfg.maxPrice || 200,
      maxPages: cfg.crawlPages || 2,
      maxItems: cfg.crawlLimit || 200,
      delayMs: 300,
      applyQualityFilter: true,
      outPrefix: `orch-${job.id}`,
    });
    appendEvent(
      job,
      "info",
      `Crawl complete — kept ${crawl?.kept ?? 0} / raw ${crawl?.rawCount ?? 0} (API total ${crawl?.apiTotal ?? "?"})`,
      { phase: "crawl" }
    );
    job.progress = { phase: "crawl", pct: 35 };
  } catch (e) {
    appendEvent(job, "warn", `Crawl soft-fail: ${e.message}`, { phase: "crawl" });
  }

  // ── Phase 3: Economics pipeline ──
  try {
    appendEvent(job, "info", "Pipeline: economics + factor verify on live candidates", { phase: "pipeline" });
    const cost = Number(cfg.cost) || 18;
    const midPrice = ((cfg.minPrice || 35) + (cfg.maxPrice || 200)) / 2;
    pipeline = await runResearchPipeline({
      category: cfg.category || "Home",
      queries: [cfg.query, ...(cfg.seedQueries || [])].filter(Boolean).slice(0, 4),
      productCostRatio: Math.min(0.85, cost / Math.max(midPrice, 1)),
      minPrice: cfg.minPrice || 35,
      maxPrice: cfg.maxPrice || 200,
      targetDailyProfit: 50,
      assumedStr: 0.015,
    });
    appendEvent(job, "info", "Pipeline complete", { phase: "pipeline" });
    job.progress = { phase: "detail", pct: 45 };
  } catch (e) {
    appendEvent(job, "warn", `Pipeline soft-fail: ${e.message}`, { phase: "pipeline" });
  }

  // ── Phase 4: Fetch REAL listing page content via getItem ──
  const boardSeed = (intel.lethalCandidates || []).slice(0, cfg.detailCount || 15);
  appendEvent(
    job,
    "info",
    `Detail: fetching Browse getItem page content for top ${boardSeed.length} products (images, description, specifics)`,
    { phase: "detail" }
  );
  const detailed = await enrichItemsWithDetails(boardSeed, {
    max: cfg.detailCount || 15,
    delayMs: cfg.detailDelayMs || 220,
  });
  const detailOk = detailed.filter((d) => d.detailFetched).length;
  appendEvent(job, "info", `Detail fetched ${detailOk}/${detailed.length} listings with full page content`, {
    phase: "detail",
  });
  job.progress = { phase: "patterns", pct: 60 };

  const medianPrice = intel.market?.priceLadder?.p50 || null;
  const products = detailed.map((it, i) =>
    toProductResearchRow(
      { ...it, rank: it.rank || i + 1 },
      {
        jobId: job.id,
        query: cfg.query,
        categoryId: cfg.categoryId,
        categoryPath: cfg.category,
        medianPrice,
      }
    )
  );

  // Also fold crawl top titles that aren't already on board (summary-only)
  for (const t of crawl?.topByPerceivedValue || []) {
    if (products.some((p) => p.title === t.title)) continue;
    if (products.length >= (cfg.detailCount || 15) + 8) break;
    products.push(
      toProductResearchRow(
        {
          id: null,
          title: t.title,
          price: t.price,
          url: t.url,
          image: null,
          images: [],
          perceivedValue: t.perceivedValue,
          scammy: t.scammy,
          descriptionText: "",
          itemSpecifics: {},
          detailFetched: false,
          rank: products.length + 1,
        },
        { jobId: job.id, query: cfg.query, categoryId: cfg.categoryId }
      )
    );
  }

  const withImages = products.filter((p) => p.image).length;
  const withUrls = products.filter((p) => p.url).length;
  if (withUrls === 0) {
    throw new Error("Hardened core: researched products missing listing URLs");
  }
  appendEvent(
    job,
    "info",
    `Research board: ${products.length} products · ${withImages} with images · ${withUrls} with listing URLs`,
    { phase: "patterns" }
  );

  // ── Phase 5: Mine patterns from real titles + descriptions ──
  const competitorTitles = products.map((p) => p.title).filter(Boolean);
  const descCorpus = products.map((p) => p.descriptionExcerpt).filter(Boolean);
  const patterns = mineKeywordPatterns([...competitorTitles, ...descCorpus]);
  // Merge content signals into buyer language
  patterns.buyerLanguage = [
    ...(patterns.buyerLanguage || []),
    ...rollupSignals(products)
      .slice(0, 5)
      .map((s) => `content:${s.signal} (${s.count})`),
  ];
  appendEvent(
    job,
    "info",
    `Patterns mined from ${competitorTitles.length} real titles + ${descCorpus.length} descriptions`,
    { phase: "patterns" }
  );

  const narrowedCategory = {
    categoryId: cfg.categoryId || products[0]?.categoryId || null,
    categoryPath:
      products.find((p) => p.categoryPath)?.categoryPath || cfg.category || "Home",
    rationale:
      (patterns.buyerLanguage || [])[0] ||
      `Narrowed from ${intel.market?.sampleSize || 0} live comps · HHI ${intel.market?.sellerConcentrationHHI}`,
    priceLadder: intel.market?.priceLadder,
    density: intel.market?.density,
  };
  appendEvent(job, "info", `Category focus → ${narrowedCategory.categoryPath}`, {
    phase: "narrow",
    narrowedCategory,
  });
  job.progress = { phase: "swarm", pct: 70 };

  // ── Phase 6: Title swarm grounded in REAL competitor language ──
  const targetVariants = Math.min(Math.max(cfg.variantCount || 200, 50), 400);
  appendEvent(
    job,
    "info",
    `Title swarm: ${targetVariants} variants from mined competitor language (not empty seed)`,
    { phase: "swarm" }
  );
  const rawVariants = generateTitleVariations({
    seed: cfg.query,
    categoryHint: narrowedCategory.categoryPath || "organizer",
    maxTitles: targetVariants,
    patterns,
  });
  const cost = Number(cfg.cost) || 18;
  const priceHint =
    Number(cfg.suggestedPrice) ||
    medianPrice ||
    Number(products[0]?.price) ||
    59.99;
  let scored = scoreVariants(rawVariants, patterns, { cost, priceHint, cfg, job });
  job.progress = { phase: "probe", pct: 80 };

  // ── Phase 7: Live probes on top title variants ──
  const probeN = Math.min(cfg.liveProbeCount ?? 12, 25);
  const isNetlify = Boolean(process.env.NETLIFY);
  const effectiveProbeN = isNetlify ? Math.min(probeN, 3) : probeN;
  appendEvent(job, "info", `Live-probing top ${effectiveProbeN} title variants`, { phase: "probe" });
  for (let i = 0; i < effectiveProbeN; i++) {
    const row = scored[i];
    if (!row) break;
    const live = await probeTitleLive(row.title, narrowedCategory.categoryId, 20);
    Object.assign(row, live);
    if (live.competitionProxy != null && live.competitionProxy > 70 && row.testPriority === "A") {
      row.testPriority = "B";
    }
    job.progress = { phase: "probe", pct: 80 + Math.round(((i + 1) / effectiveProbeN) * 10) };
    persist(job);
    await sleep(cfg.probeDelayMs || 350);
  }

  // ── Phase 8: Spreadsheets ──
  appendEvent(job, "info", "Writing product research + title decision spreadsheets", { phase: "log" });
  const topForSheet = scored.slice(0, Math.min(cfg.sheetRows || 150, scored.length));
  // Attach best competitor image URL as reference for outrank tests
  const refImage = products.find((p) => p.image)?.image;
  const refUrl = products.find((p) => p.url)?.url;
  for (const row of topForSheet) {
    row.refCompetitorImage = refImage;
    row.refCompetitorUrl = refUrl;
    row.contentSignals = extractContentSignals(row.title, row.title, {});
  }
  const sheet = toDecisionCsv(topForSheet, {
    jobId: job.id,
    query: cfg.query,
    categoryId: narrowedCategory.categoryId,
    categoryPath: narrowedCategory.categoryPath,
    landedCost: cost,
    suggestedPrice: priceHint,
    loggedAt: new Date().toISOString(),
  });

  job.results = buildResults({
    job,
    products,
    intel,
    patterns,
    narrowedCategory,
    scored,
    sheet,
    pipeline,
  });

  job.progress = { phase: "done", pct: 100 };
  job.status = "completed";
  job.updatedAt = new Date().toISOString();
  appendEvent(
    job,
    "info",
    `Mission complete — ${products.length} real products (${withImages} images) · ${sheet.rows.length} title tests · ${job.results.recommendations.productsToBeat.length} to beat`,
    { phase: "done" }
  );
  persist(job);
  bus.emit("complete", { jobId: job.id });
  return job;
}

export function deployMission(config = {}, { sync = false } = {}) {
  const job = {
    id: id(),
    status: "queued",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    config: {
      query: String(config.query || config.q || "").trim(),
      categoryId: config.categoryId || config.category_ids || null,
      category: config.category || config.categoryLabel || "Home",
      cost: config.cost != null ? Number(config.cost) : 18,
      altCost: config.altCost != null ? Number(config.altCost) : undefined,
      minPrice: config.minPrice != null ? Number(config.minPrice) : 35,
      maxPrice: config.maxPrice != null ? Number(config.maxPrice) : 200,
      suggestedPrice: config.suggestedPrice != null ? Number(config.suggestedPrice) : undefined,
      variantCount: config.variantCount != null ? Number(config.variantCount) : 200,
      liveProbeCount: config.liveProbeCount != null ? Number(config.liveProbeCount) : 12,
      sheetRows: config.sheetRows != null ? Number(config.sheetRows) : 150,
      seedQueries: config.seedQueries || [],
      brandSafe: config.brandSafe !== false,
      probeDelayMs: config.probeDelayMs || 350,
      crawlLimit: config.crawlLimit || 200,
      crawlPages: config.crawlPages || 2,
      intelLimit: config.intelLimit || 100,
      detailCount: config.detailCount != null ? Number(config.detailCount) : 12,
      detailDelayMs: config.detailDelayMs || 220,
      dryRun: Boolean(config.dryRun),
    },
    progress: { phase: "queued", pct: 0 },
    events: [],
    results: null,
    error: null,
  };

  if (!job.config.query) {
    job.status = "failed";
    job.error = "query required";
    appendEvent(job, "error", "Deploy rejected — query required");
    jobs.set(job.id, job);
    persist(job);
    return job;
  }

  jobs.set(job.id, job);
  appendEvent(job, "info", "Job queued — hardened research core", { phase: "queued" });

  const run = async () => {
    try {
      await runMission(job);
    } catch (e) {
      job.status = "failed";
      job.error = e.message || String(e);
      job.updatedAt = new Date().toISOString();
      appendEvent(job, "error", `Mission failed: ${job.error}`, { phase: "error" });
      persist(job);
      bus.emit("failed", { jobId: job.id, error: job.error });
    }
  };

  if (sync) return run().then(() => job);
  setImmediate(() => run());
  return job;
}

export function getJobEvents(jobId, afterIndex = 0) {
  const job = getJob(jobId);
  if (!job) return null;
  return {
    jobId,
    status: job.status,
    progress: job.progress,
    events: job.events.slice(afterIndex),
    nextIndex: job.events.length,
  };
}

export function getJobSpreadsheet(jobId, { workbook = false, products = false } = {}) {
  const job = getJob(jobId);
  if (!job) return null;
  if (!job.results?.spreadsheetCsv && !job.results?.productSpreadsheetCsv) {
    return { jobId, ready: false, status: job.status };
  }
  let csv = job.results.spreadsheetCsv;
  if (workbook && job.results.workbookCsv) csv = job.results.workbookCsv;
  if (products && job.results.productSpreadsheetCsv) csv = job.results.productSpreadsheetCsv;
  return {
    jobId,
    ready: true,
    status: job.status,
    csv,
    rows: products ? job.results.products : job.results.variants,
    products: job.results.products,
    columns: job.results.columns,
    recommendations: job.results.recommendations,
    gallery: job.results.gallery,
    intel: job.results.intel,
  };
}

export { bus, DATA_DIR };
