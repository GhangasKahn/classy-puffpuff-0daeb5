/**
 * Playground job runner — dispatches sub-agents to real LPROS workers.
 */
import {
  expectedDailyProfit,
  listingsNeeded,
  netProfitPerSale,
  stressForecast,
} from "../../../lpros/src/core/economics.js";
import { hardenCandidate } from "../../../lpros/src/core/evidence.js";
import { draftListing } from "../../../lpros/src/agents/listing.js";
import { fulfillDecision } from "../fulfill/adapter.js";
import { getAgent } from "./catalog.js";
import { appendEvent, load, persist } from "./store.js";
import { runBrowserJob } from "./browser.js";
import { runVmJob } from "./vm.js";
import { deskFromResearch, deskFromPlaygroundJobs, emptyLiveHint, noLiveProductsError } from "../http/marketRows.js";

function num(v, d = null) {
  if (v == null || v === "") return d;
  const n = Number(v);
  return Number.isFinite(n) ? n : d;
}

function meuftBrief({ input = {}, childResults = [], econ = null }) {
  const q = input.q || input.title || "unspecified query";
  const sold = num(input.soldCount);
  const cost = num(input.productCost ?? input.cost);
  const alt = num(input.altProductCost);
  const price = num(input.price ?? input.salePrice ?? input.suggestedPrice, 49);
  const flags = [];
  if (sold == null) flags.push("sold_evidence_missing");
  if (cost == null) flags.push("product_cost_missing");
  if (alt == null) flags.push("alt_cost_missing");
  const childFails = childResults.filter((c) => c.status === "failed");
  if (childFails.length) flags.push("soldier_failed");
  const verdict = flags.length ? "CONDITIONAL" : "PASS_READY";
  const known = [];
  const estimated = [];
  const assumed = [];
  if (sold != null) known.push(`soldCount=${sold}`);
  else assumed.push("soldCount unknown — Insights/Terapeak gated");
  if (cost != null) known.push(`productCost=${cost}`);
  else assumed.push("landed cost unknown");
  const intel = childResults.find((c) => c.agent === "intel" && c.result?.market);
  if (intel?.result?.market?.priceLadder) {
    known.push(`ladder p50=${intel.result.market.priceLadder.p50}`);
  } else {
    estimated.push("price ladder from soldiers not present");
  }
  return {
    mission: `Evaluate "${q}" for dropshipping lethality (high PV, fee-true net, no scam lots)`,
    economics: econ,
    uncertainty: { known, estimated, assumed },
    factors: { verdict, flags },
    verdict,
    soldiers: childResults.map((c) => ({
      id: c.id,
      agent: c.agent,
      status: c.status,
      error: c.error || null,
    })),
    next:
      verdict === "PASS_READY"
        ? ["Promote package to SKU registry", "Original photos", "Export Seller Hub CSV"]
        : [
            "Browser playbook: Terapeak sold count",
            "Dual supplier quotes → productCost + altProductCost",
            "Re-run Evidence soldier",
          ],
    accuracyAudit: "ran",
    caveat: "Brain never fabricates eBay sold counts. CTR/STR are Browse proxies.",
  };
}

async function runEconomics(input = {}) {
  const price = num(input.price ?? input.salePrice ?? input.suggestedPrice, 49);
  const cost = num(input.cost ?? input.productCost, price * num(input.costRatio, 0.4));
  const net = netProfitPerSale({
    salePrice: price,
    productCost: cost,
    returnsBufferRate: num(input.returns, 0.04),
  });
  const listings = num(input.listings, 300);
  const str = num(input.str, 0.015);
  const target = num(input.target, 50);
  return {
    net,
    forecast: {
      expected: expectedDailyProfit({ listings, str, avgNet: net.net }),
      needed: listingsNeeded({ targetDailyProfit: target, str, avgNet: net.net }),
      stress: stressForecast({ listings, str, avgNet: net.net, targetDailyProfit: target }),
    },
  };
}

async function runScout(input = {}) {
  if (input.dryRun) {
    return {
      dryRun: true,
      top: [
        {
          title: `Solid wood ${input.q || "desk organizer"} oak desktop storage`,
          salePrice: 49,
          perceivedValue: 0.62,
          source: "dry-fixture",
        },
      ],
      note: "Dry-run fixture — live Scout uses Browse pipeline",
    };
  }
  const { runResearchPipeline } = await import("../../../lpros/src/pipeline.js");
  const out = await runResearchPipeline({
    category: input.categoryLabel || "Home",
    queries: [input.q || "desk organizer"],
    productCostRatio: num(input.costRatio, 0.4),
    minPrice: num(input.minPrice, 35),
    maxPrice: num(input.maxPrice, 150),
    targetDailyProfit: num(input.target, 50),
    assumedStr: num(input.str, 0.015),
  });
  const desk = deskFromResearch({
    top: out.top,
    marketBoard: out.market?.board,
    viz: out.market?.viz,
  });
  if (!desk.productCount) {
    throw noLiveProductsError(`Scout: 0 live products. ${emptyLiveHint()}`);
  }
  return {
    top: (out.top || []).slice(0, 12),
    products: desk.products,
    productCount: desk.productCount,
    productsWithImages: desk.productsWithImages,
    productsWithUrls: desk.productsWithUrls,
    market: out.market || null,
    viz: out.viz || out.market?.viz || null,
    algorithm: out.algorithm || out.market?.algorithm,
  };
}

async function runIntel(input = {}) {
  if (input.dryRun) {
    return {
      dryRun: true,
      market: {
        sampleSize: 3,
        priceLadder: { p10: 35, p50: 49, p75: 62, p90: 80 },
        sellerConcentrationHHI: 0.12,
      },
      lethalCandidates: [],
      note: "Dry-run fixture — live Intel uses Browse search",
    };
  }
  const { competitorIntel } = await import("../intel/competitor.js");
  const intel = await competitorIntel({
    q: input.q || "desk organizer",
    categoryId: input.categoryId || "25339",
    minPrice: num(input.minPrice, 35),
    maxPrice: num(input.maxPrice, 150),
    limit: num(input.limit, 80),
    productCostRatio: num(input.costRatio, 0.4),
  });
  const desk = deskFromResearch(intel);
  if (!desk.productCount) {
    throw noLiveProductsError(`Intel: 0 live products. ${intel.emptyReason || emptyLiveHint()}`);
  }
  return { ...intel, products: desk.products, productCount: desk.productCount };
}

async function runCrawler(input = {}) {
  if (input.dryRun) {
    return { dryRun: true, skipped: true, note: "Crawler skipped in dry-run" };
  }
  const { crawlCategory } = await import("../../../lpros/src/agents/crawl.js");
  const crawl = await crawlCategory({
    categoryId: input.categoryId || "25339",
    q: input.q,
    minPrice: num(input.minPrice, 35),
    maxPrice: num(input.maxPrice, 150),
    maxPages: num(input.crawlPages, 2),
    maxItems: num(input.crawlPages, 2) * 200,
    delayMs: 300,
    applyQualityFilter: true,
    outPrefix: `pg-crawl-${input.categoryId || "25339"}`,
  });
  return {
    itemCount: crawl?.kept ?? crawl?.items?.length ?? 0,
    items: (crawl?.topByPerceivedValue || []).slice(0, 40),
    products: (crawl?.topByPerceivedValue || []).slice(0, 40),
    topByPerceivedValue: (crawl?.topByPerceivedValue || []).slice(0, 8),
  };
}

async function runEvidence(input = {}) {
  return hardenCandidate(
    {
      title: input.title || input.q || "Candidate",
      salePrice: num(input.salePrice ?? input.price, 49),
      perceivedValue: num(input.perceivedValue, 0.55),
    },
    {
      soldCount: num(input.soldCount),
      productCost: num(input.productCost ?? input.cost),
      altProductCost: num(input.altProductCost),
      leadTimeDays: num(input.leadTimeDays, 7),
      demandSource: input.demandSource || "terapeak",
    }
  );
}

async function runCopy(input = {}) {
  return {
    draft: draftListing({
      title: input.title || input.q || "Solid wood desk organizer",
      salePrice: num(input.salePrice ?? input.price, 49),
      condition: input.condition || "New",
    }),
  };
}

async function runFactory(input = {}) {
  if (!input.orchJobId) {
    throw Object.assign(new Error("orchJobId required for factory soldier"), { status: 400 });
  }
  const { packagesForJob } = await import("../orchestrate/factory.js");
  const factory = packagesForJob(input.orchJobId, { maxPackages: num(input.maxPackages, 12) });
  if (!factory) throw Object.assign(new Error("orch job not found"), { status: 404 });
  return {
    packageCount: factory.packageCount,
    clusters: factory.clusters,
    packages: (factory.packages || []).slice(0, 8),
  };
}

async function runFulfill(input = {}) {
  return fulfillDecision(
    {
      buyerTotal: num(input.buyerTotal, 54),
      supplierCost: num(input.supplierCost),
      supplierLeadDays: num(input.supplierLeadDays, 9),
      margin: num(input.margin, 0.2),
      supplierConfirmed: Boolean(input.supplierConfirmed),
      policyCompliant: input.policyCompliant !== false,
      lineItems: [{ sku: input.sku || "demo" }],
    },
    {}
  );
}

async function runSwarm(input = {}) {
  if (input.dryRun) {
    const econ = await runEconomics(input);
    return {
      dryRun: true,
      brief: meuftBrief({ input, econ: econ.net, childResults: [] }),
      note: "Dry swarm — live path is POST /swarm",
    };
  }
  const { runResearchSwarm } = await import("../swarm/research.js");
  return runResearchSwarm({
    q: input.q,
    categoryId: input.categoryId,
    minPrice: num(input.minPrice, 35),
    maxPrice: num(input.maxPrice, 150),
    costRatio: num(input.costRatio, 0.4),
    deepCrawl: Boolean(input.deepCrawl),
    evidencePack:
      num(input.soldCount) != null
        ? {
            soldCount: num(input.soldCount),
            productCost: num(input.productCost),
            altProductCost: num(input.altProductCost),
            leadTimeDays: num(input.leadTimeDays, 7),
          }
        : null,
  });
}

async function runBrain(job, input = {}) {
  const childResults = [];
  for (const cid of job.children || []) {
    const child = load("job", cid);
    if (child) childResults.push(child);
  }
  const econ = await runEconomics(input);
  const brief = meuftBrief({ input, childResults, econ: econ.net });
  const desk = deskFromPlaygroundJobs(childResults, { query: input.q, dryRun: Boolean(input.dryRun) });
  if (!input.dryRun && !desk.productCount) {
    brief.verdict = "NO-GO";
    brief.emptyReason = desk.emptyReason;
    brief.next = [
      "Run Live product research (not Dry-run)",
      "Confirm EBAY_PRD_APP_ID / EBAY_PRD_CERT_ID and EBAY_ENV=production",
      "Use local Command :8790 if Netlify env vars are unset",
    ];
  }
  return {
    brief,
    economics: econ,
    products: desk.products,
    productCount: desk.productCount,
    productsWithImages: desk.productsWithImages,
    productsWithUrls: desk.productsWithUrls,
    dryRun: desk.dryRun,
    emptyReason: desk.emptyReason,
  };
}

async function dispatch(job) {
  const input = job.input || {};
  const agent = job.agent || (job.kind === "browser" ? "browser" : job.kind === "vm" ? "vm" : null);
  switch (agent) {
    case "brain":
      return runBrain(job, input);
    case "scout":
      return runScout(input);
    case "intel":
      return runIntel(input);
    case "crawler":
      return runCrawler(input);
    case "economics":
      return runEconomics(input);
    case "evidence":
      return runEvidence(input);
    case "copy":
      return runCopy(input);
    case "factory":
      return runFactory(input);
    case "fulfill":
      return runFulfill(input);
    case "swarm":
      return runSwarm(input);
    case "browser":
      return runBrowserJob(input);
    case "vm":
      return runVmJob(input);
    default:
      if (job.kind === "browser") return runBrowserJob(input);
      if (job.kind === "vm") return runVmJob(input);
      throw Object.assign(new Error(`unknown agent: ${agent || job.kind}`), { status: 400 });
  }
}

export async function executeJob(jobId) {
  const job = load("job", jobId);
  if (!job) throw Object.assign(new Error("job not found"), { status: 404 });
  if (job.status === "cancelled" || job.cancelRequested) {
    job.status = "cancelled";
    persist("job", job);
    return job;
  }
  job.status = "running";
  job.progress = { phase: "start", pct: 5 };
  job.startedAt = new Date().toISOString();
  appendEvent(job, "info", `Running ${job.agent || job.kind}`, { phase: "start" });

  try {
    if (job.children?.length) {
      appendEvent(job, "info", `Spawning ${job.children.length} soldiers`, { phase: "spawn" });
      job.progress = { phase: "soldiers", pct: 20 };
      persist("job", job);
      await Promise.all(
        job.children.map(async (cid) => {
          const child = load("job", cid);
          if (!child || child.status === "cancelled") return;
          await executeJob(cid);
        })
      );
    }
    if (job.cancelRequested) {
      job.status = "cancelled";
      appendEvent(job, "warn", "Cancelled before dispatch complete", { phase: "cancel" });
      return job;
    }
    job.progress = { phase: "dispatch", pct: 60 };
    persist("job", job);
    const result = await dispatch(job);
    job.result = result;
    job.status = "done";
    job.progress = { phase: "done", pct: 100 };
    job.finishedAt = new Date().toISOString();
    appendEvent(job, "info", "Complete", { phase: "done" });
    return job;
  } catch (e) {
    job.status = "failed";
    job.error = e.message || String(e);
    job.progress = { phase: "failed", pct: job.progress?.pct || 0 };
    job.finishedAt = new Date().toISOString();
    appendEvent(job, "error", job.error, { phase: "failed" });
    return job;
  }
}

export function agentMeta(id) {
  return getAgent(id);
}
