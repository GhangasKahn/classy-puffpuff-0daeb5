/**
 * Agent orchestration job store + async mission runner.
 * Deploy → research/crawl → pattern mine → title swarm → score → spreadsheet log.
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
import { netProfitPerSale } from "../../../lpros/src/core/economics.js";
import { searchActiveListings } from "../../../ebay-sold-items/src/ebay/browse.js";
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
    fs.writeFileSync(path.join(DATA_DIR, `${job.id}.json`), JSON.stringify(job, null, 2));
  } catch {
    /* ignore */
  }
}

function appendEvent(job, level, message, data = {}) {
  const ev = {
    at: new Date().toISOString(),
    level,
    message,
    ...data,
  };
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
      variantCount: j.results?.variants?.length || 0,
      error: j.error || null,
    }));
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/** Offline mission for tests / no credentials — still produces full spreadsheet. */
async function runDryMission(job) {
  const cfg = job.config;
  appendEvent(job, "info", "Dry-run mode — synthetic competitor corpus (no eBay calls)", {
    phase: "crawl",
  });
  job.progress = { phase: "patterns", pct: 30 };
  const seedTitles = [
    `Solid wood ${cfg.query} oak desktop storage`,
    `Bamboo ${cfg.query} clutter solution home office`,
    `Walnut desk organizer multi-tier upgrade`,
    `Premium hardwood mail sorter drawer tray`,
    `Minimalist metal desk organizer cable management`,
    `Heavy duty stackable desk storage tray set`,
    ...((cfg.seedQueries || []).map((q) => `${q} organizer wood`)),
  ];
  const patterns = mineKeywordPatterns(seedTitles);
  appendEvent(job, "info", `Patterns from ${seedTitles.length} synthetic titles`, { phase: "patterns" });

  const narrowedCategory = {
    categoryId: cfg.categoryId || "25339",
    categoryPath: cfg.category || "Home",
    rationale: "Dry-run category seed",
  };
  const targetVariants = Math.min(Math.max(cfg.variantCount || 80, 20), 200);
  job.progress = { phase: "swarm", pct: 50 };
  appendEvent(job, "info", `Generating ${targetVariants} title variations`, { phase: "swarm" });
  const rawVariants = generateTitleVariations({
    seed: cfg.query,
    categoryHint: "organizer",
    maxTitles: targetVariants,
    patterns,
  });

  const cost = Number(cfg.cost) || 18;
  const priceHint = Number(cfg.suggestedPrice) || 59.99;
  const scored = rawVariants
    .filter((v) => !v.scammy)
    .map((v) => {
      const seo = scoreTitleSeo(v.title, patterns, { salePrice: priceHint });
      const kw = extractKeywordsFromTitle(v.title, patterns);
      const econ = netProfitPerSale({ salePrice: priceHint, productCost: cost });
      const imageSeo = imageSeoChecklist({ title: v.title, primaryKeyword: kw.primaryKeyword });
      const description = buildConversionDescription({
        title: v.title,
        keywords: kw.secondaryKeywords,
        price: priceHint,
      });
      const seoPct = Math.round((seo.seoScore || 0) * 100);
      return {
        ...v,
        seoScore: seoPct,
        primaryKeyword: kw.primaryKeyword,
        secondaryKeywords: kw.secondaryKeywords,
        suggestedPrice: priceHint,
        landedCost: cost,
        estFees: econ.fees,
        estNet: econ.net,
        estMarginPct: econ.marginPct,
        imageSeo,
        description,
        liveTotal: 1200 + Math.round(seoPct * 8),
        liveMedianPrice: priceHint,
        liveImageCoverage: 0.72,
        competitionProxy: Math.min(100, Math.round(seoPct * 0.6)),
        variantFamily: v.family || "base",
        testPriority: seoPct >= 70 ? "A" : seoPct >= 55 ? "B" : "C",
      };
    })
    .sort((a, b) => (b.seoScore || 0) - (a.seoScore || 0));

  job.progress = { phase: "log", pct: 90 };
  const topForSheet = scored.slice(0, Math.min(cfg.sheetRows || 100, scored.length));
  const sheet = toDecisionCsv(topForSheet, {
    jobId: job.id,
    query: cfg.query,
    categoryId: narrowedCategory.categoryId,
    categoryPath: narrowedCategory.categoryPath,
    landedCost: cost,
    suggestedPrice: priceHint,
    loggedAt: new Date().toISOString(),
  });

  job.results = {
    narrowedCategory,
    patterns: {
      topKeywords: (patterns.topUnigrams || []).slice(0, 20),
      buyerPhrases: patterns.buyerLanguage || [],
    },
    pipelineSummary: { dryRun: true },
    variants: sheet.rows,
    variantTotalGenerated: scored.length,
    spreadsheetCsv: sheet.csv,
    columns: sheet.columns,
    recommendations: {
      testNow: sheet.rows.filter((r) => r.decision === "TEST_NOW").slice(0, 15),
      rewrite: sheet.rows.filter((r) => r.decision === "REWRITE").slice(0, 10),
      imagePriority: sheet.rows
        .filter((r) => (r.imageActions || []).length)
        .slice(0, 10)
        .map((r) => ({ title: r.title, actions: r.imageActions })),
    },
  };
  job.progress = { phase: "done", pct: 100 };
  job.status = "completed";
  job.updatedAt = new Date().toISOString();
  appendEvent(
    job,
    "info",
    `Dry mission complete — ${sheet.rows.length} spreadsheet rows; ${job.results.recommendations.testNow.length} TEST_NOW`,
    { phase: "done" }
  );
  persist(job);
  bus.emit("complete", { jobId: job.id });
  return job;
}

async function probeTitleLive(title, categoryId, limit = 20) {
  try {
    const res = await searchActiveListings({
      q: title.slice(0, 80),
      categoryIds: categoryId || undefined,
      limit,
      sort: "bestMatch",
    });
    const items = res.items || res.itemSummaries || [];
    const prices = items
      .map((it) => Number(it.price?.value ?? it.price))
      .filter((n) => Number.isFinite(n))
      .sort((a, b) => a - b);
    const withImg = items.filter(
      (it) =>
        it.image?.imageUrl ||
        it.image ||
        (it.thumbnailImages || [])[0]?.imageUrl ||
        (it.images || [])[0]
    ).length;
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

/**
 * Core mission phases — no manual steps required once deployed.
 */
export async function runMission(job) {
  const cfg = job.config;
  await loadEbayEnv();
  job.status = "running";
  job.updatedAt = new Date().toISOString();
  appendEvent(job, "info", "Mission deployed — agents starting research crawl", { phase: "deploy" });
  job.progress = { phase: "crawl", pct: 5 };

  if (cfg.dryRun) {
    return runDryMission(job);
  }

  let crawl = null;
  let pipeline = null;
  let intel = null;

  // Phase 1: light category crawl sample
  try {
    appendEvent(job, "info", `Crawling category market for "${cfg.query}"`, {
      phase: "crawl",
      categoryId: cfg.categoryId,
    });
    crawl = await crawlCategory({
      categoryId: cfg.categoryId,
      q: cfg.query,
      minPrice: cfg.minPrice || 35,
      maxPrice: cfg.maxPrice || 200,
      maxPages: cfg.crawlPages || 1,
      maxItems: cfg.crawlLimit || 80,
      delayMs: 300,
      applyQualityFilter: true,
      outPrefix: `orch-${job.id}`,
    });
    job.progress = { phase: "crawl", pct: 20 };
    appendEvent(
      job,
      "info",
      `Crawl complete — kept ${crawl?.kept ?? 0} / raw ${crawl?.rawCount ?? 0}`,
      { phase: "crawl" }
    );
  } catch (e) {
    appendEvent(job, "warn", `Crawl soft-fail: ${e.message} — continuing with pipeline sample`, {
      phase: "crawl",
    });
  }

  // Phase 1b: competitor intel (titles for pattern mining)
  try {
    appendEvent(job, "info", "Pulling competitor density + listing titles", { phase: "crawl" });
    intel = await competitorIntel({
      q: cfg.query,
      categoryId: cfg.categoryId,
      minPrice: cfg.minPrice || 35,
      maxPrice: cfg.maxPrice || 200,
      limit: 100,
      productCostRatio: Math.min(
        0.85,
        (Number(cfg.cost) || 18) / Math.max(((cfg.minPrice || 35) + (cfg.maxPrice || 200)) / 2, 1)
      ),
    });
  } catch (e) {
    appendEvent(job, "warn", `Intel soft-fail: ${e.message}`, { phase: "crawl" });
  }

  // Phase 2: economics + verify pipeline
  try {
    appendEvent(job, "info", "Running economics + Bayesian-lite + factor verify pipeline", {
      phase: "intel",
    });
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
    job.progress = { phase: "intel", pct: 40 };
    appendEvent(job, "info", `Intel ready — ranked ${pipeline?.ranked?.length || pipeline?.market?.ranked?.length || 0}`, {
      phase: "intel",
    });
  } catch (e) {
    appendEvent(job, "warn", `Pipeline soft-fail: ${e.message}`, { phase: "intel" });
  }

  // Phase 3: decipher competitor title patterns
  appendEvent(job, "info", "Mining competitor titles for buyer-language patterns", { phase: "patterns" });
  const competitorTitles = [];
  const itemPool = [
    ...(intel?.lethalCandidates || []),
    ...(crawl?.topByPerceivedValue || []),
    ...(pipeline?.market?.ranked || pipeline?.ranked || []),
    ...(pipeline?.candidates || []),
  ].slice(0, 150);
  for (const it of itemPool) {
    if (it.title) competitorTitles.push(it.title);
  }
  const patterns = mineKeywordPatterns(competitorTitles);
  job.progress = { phase: "patterns", pct: 50 };
  const topTerms = (patterns.topUnigrams || []).slice(0, 5).map((k) => k.term).join(", ");
  appendEvent(
    job,
    "info",
    `Patterns extracted — ${patterns.sampleSize} titles, top: ${topTerms || "n/a"}`,
    { phase: "patterns" }
  );

  // Phase 4: narrow category signal
  const narrowedCategory = {
    categoryId: cfg.categoryId || null,
    categoryPath: cfg.category || "Home",
    rationale:
      (patterns.buyerLanguage || [])[0] ||
      "Use seed category; refine by attribute density in mined titles",
  };
  appendEvent(
    job,
    "info",
    `Category narrowed → ${narrowedCategory.categoryPath || narrowedCategory.categoryId || "open"}`,
    { phase: "narrow", narrowedCategory }
  );
  job.progress = { phase: "swarm", pct: 55 };

  // Phase 5: title / keyword variation swarm (100s locally)
  const targetVariants = Math.min(Math.max(cfg.variantCount || 200, 50), 400);
  appendEvent(job, "info", `Generating ${targetVariants} title/keyword variations`, { phase: "swarm" });
  const rawVariants = generateTitleVariations({
    seed: cfg.query,
    categoryHint: narrowedCategory.categoryPath || "organizer",
    maxTitles: targetVariants,
    patterns,
  });
  appendEvent(job, "info", `Swarm produced ${rawVariants.length} title candidates`, { phase: "swarm" });

  // Phase 6: SEO score + economics + image/description packs
  appendEvent(job, "info", "Scoring SEO, attaching cost bands, building image + description packs", {
    phase: "score",
  });
  const cost = Number(cfg.cost) || 18;
  const priceHint =
    Number(cfg.suggestedPrice) ||
    Number(pipeline?.market?.ranked?.[0]?.salePrice) ||
    Number(pipeline?.ranked?.[0]?.salePrice) ||
    59.99;

  let scored = rawVariants
    .filter((v) => !v.scammy)
    .map((v, idx) => {
      const seo = scoreTitleSeo(v.title, patterns, {
        salePrice: priceHint,
        categoryMedianPrice: priceHint * 0.92,
      });
      const kw = extractKeywordsFromTitle(v.title, patterns);
      const econ = netProfitPerSale({
        salePrice: priceHint,
        productCost: cost,
      });
      const imageSeo = imageSeoChecklist({
        title: v.title,
        primaryKeyword: kw.primaryKeyword,
      });
      const description = buildConversionDescription({
        title: v.title,
        keywords: kw.secondaryKeywords,
        material: (patterns.materialDemand || [])[0]?.term,
        price: priceHint,
      });
      const seoPct = Math.round((seo.seoScore || 0) * 100);
      return {
        ...v,
        idx,
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
      };
    });

  scored.sort((a, b) => (b.seoScore || 0) - (a.seoScore || 0));
  job.progress = { phase: "probe", pct: 70 };

  // Phase 7: live Browse probes on top N (rate-limit friendly)
  const probeN = Math.min(cfg.liveProbeCount ?? 12, 25);
  const isNetlify = Boolean(process.env.NETLIFY);
  const effectiveProbeN = isNetlify ? Math.min(probeN, 3) : probeN;
  appendEvent(
    job,
    "info",
    `Live-probing top ${effectiveProbeN} titles for competition / image coverage`,
    { phase: "probe" }
  );
  for (let i = 0; i < effectiveProbeN; i++) {
    const row = scored[i];
    if (!row) break;
    const live = await probeTitleLive(row.title, narrowedCategory.categoryId, 20);
    Object.assign(row, live);
    if (live.competitionProxy != null && live.competitionProxy > 70 && row.testPriority === "A") {
      row.testPriority = "B";
    }
    appendEvent(
      job,
      "debug",
      `Probed #${i + 1}: total=${live.liveTotal ?? "n/a"} img=${live.liveImageCoverage ?? "n/a"}`,
      { phase: "probe", i }
    );
    job.progress = { phase: "probe", pct: 70 + Math.round(((i + 1) / effectiveProbeN) * 15) };
    persist(job);
    await sleep(cfg.probeDelayMs || 350);
  }

  // Phase 8: spreadsheet decision log
  appendEvent(job, "info", "Writing decision spreadsheet (CSV) for test selection", { phase: "log" });
  const topForSheet = scored.slice(0, Math.min(cfg.sheetRows || 150, scored.length));
  const sheet = toDecisionCsv(topForSheet, {
    jobId: job.id,
    query: cfg.query,
    categoryId: narrowedCategory.categoryId,
    categoryPath: narrowedCategory.categoryPath,
    landedCost: cost,
    suggestedPrice: priceHint,
    loggedAt: new Date().toISOString(),
  });

  job.results = {
    narrowedCategory,
    patterns: {
      topKeywords: (patterns.topUnigrams || []).slice(0, 30),
      topBigrams: (patterns.topBigrams || []).slice(0, 20),
      buyerPhrases: patterns.buyerLanguage || [],
      attributeHints: patterns.materialDemand || [],
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
    columns: sheet.columns,
    recommendations: {
      testNow: sheet.rows.filter((r) => r.decision === "TEST_NOW").slice(0, 15),
      rewrite: sheet.rows.filter((r) => r.decision === "REWRITE").slice(0, 10),
      imagePriority: sheet.rows
        .filter((r) => (r.imageActions || []).length)
        .slice(0, 10)
        .map((r) => ({ title: r.title, actions: r.imageActions })),
    },
  };

  job.progress = { phase: "done", pct: 100 };
  job.status = "completed";
  job.updatedAt = new Date().toISOString();
  appendEvent(
    job,
    "info",
    `Mission complete — ${sheet.rows.length} rows logged; ${job.results.recommendations.testNow.length} marked TEST_NOW`,
    { phase: "done" }
  );
  persist(job);
  bus.emit("complete", { jobId: job.id });
  return job;
}

/**
 * Deploy a mission (async by default).
 * On Netlify, prefer sync:true with reduced probes (function timeout).
 */
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
      crawlLimit: config.crawlLimit || 80,
      crawlPages: config.crawlPages || 1,
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
  appendEvent(job, "info", "Job queued for agent deployment", { phase: "queued" });

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

  if (sync) {
    return run().then(() => job);
  }
  setImmediate(() => {
    run();
  });
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

export function getJobSpreadsheet(jobId) {
  const job = getJob(jobId);
  if (!job) return null;
  if (!job.results?.spreadsheetCsv) {
    return { jobId, ready: false, status: job.status };
  }
  return {
    jobId,
    ready: true,
    status: job.status,
    csv: job.results.spreadsheetCsv,
    rows: job.results.variants,
    columns: job.results.columns,
    recommendations: job.results.recommendations,
  };
}

export { bus, DATA_DIR };
