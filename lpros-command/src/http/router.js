/**
 * Shared HTTP API router — used by local server and Netlify function.
 * Returns { status, body, type } where body is object or string.
 */
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runResearchSwarm } from "../swarm/research.js";
import { competitorIntel } from "../intel/competitor.js";
import { fulfillDecision, providerMatrix } from "../fulfill/adapter.js";
import {
  netProfitPerSale,
  listingsNeeded,
  expectedDailyProfit,
  stressForecast,
} from "../../../lpros/src/core/economics.js";
import { hardenCandidate } from "../../../lpros/src/core/evidence.js";
import { draftListing } from "../../../lpros/src/agents/listing.js";
import {
  readRecentOutcomes,
  recordSaleOutcome,
  logOutcome,
} from "../../../lpros/src/agents/outcome.js";
import { listSkus, promoteCandidate, getSku, setSkuStatus, removeSku } from "../ops/skus.js";
import { exportPackages, buildListingPackage } from "../ops/packages.js";
import { listOrders, ingestOrder, attachTracking } from "../ops/orders.js";
import { authStatus } from "../ebay/userToken.js";
import { config as ebayConfig } from "../../../ebay-sold-items/src/config.js";
import { deskFromPlaygroundJobs, deskFromResearch, emptyLiveHint } from "./marketRows.js";
import { enrichItemsWithDetails } from "../../../ebay-sold-items/src/ebay/browse.js";
import {
  cancelWatch,
  createWatchSession,
  getWatch,
  listWatches,
  slimWatch,
  tickWatch,
} from "../research/watch.js";
import { dryRunPublish, publishSku } from "../ebay/inventory.js";
import { pushTracking, pullOrders } from "../ebay/fulfillment.js";
import { rankMarket } from "../../../lpros/src/core/ranker.js";
import { applyFilters } from "../../../lpros/src/core/filters.js";
import { computeMarketMetrics } from "../../../lpros/src/core/market_metrics.js";
import {
  deployMission,
  getJob,
  listJobs,
  getJobEvents,
  getJobSpreadsheet,
} from "../orchestrate/runner.js";
import {
  deployCampaign,
  getCampaignJob,
  getCampaignEvents,
  getCampaignSpreadsheet,
  listCampaignJobs,
  DEFAULT_MARATHON_CATEGORIES,
  cancelCampaign,
  resumeCampaign,
} from "../orchestrate/campaign.js";
import { assemblePackages, promotePackages } from "../orchestrate/factory.js";
import { requestCancel } from "../orchestrate/jobstore.js";
import {
  AGENT_CATALOG,
  PLAYBOOKS,
  PRESETS,
  VM_RECIPES,
  activityFeed,
  addCapture,
  advanceSession,
  applySessionEvidence,
  boardSummary,
  cancelJob,
  commentJob,
  createJob,
  createSession,
  fetchAllowed,
  getJob as getPlaygroundJob,
  getSession,
  jobTree,
  launchAgent,
  listJobs as listPlaygroundJobs,
  listKind,
  listPacks,
  listSessions,
  persist,
  promoteFromJob,
  retryJob,
  runRecipe,
  setJobStatus,
  slimJob,
  startJob,
  vmSnapshot,
  WORKLOADS,
  runWorkload,
  listComms,
  runConditioner,
} from "../playground/index.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

function evidenceFromBody(b) {
  if (!b || typeof b !== "object") return null;
  const pack = {};
  if (b.soldCount != null && b.soldCount !== "") pack.soldCount = Number(b.soldCount);
  if (b.avgSoldPrice != null && b.avgSoldPrice !== "") pack.avgSoldPrice = Number(b.avgSoldPrice);
  if (b.sellThrough != null && b.sellThrough !== "") pack.sellThrough = Number(b.sellThrough);
  if (b.productCost != null && b.productCost !== "") pack.productCost = Number(b.productCost);
  if (b.altProductCost != null && b.altProductCost !== "") pack.altProductCost = Number(b.altProductCost);
  if (b.leadTimeDays != null && b.leadTimeDays !== "") pack.leadTimeDays = Number(b.leadTimeDays);
  if (b.demandSource) pack.demandSource = String(b.demandSource);
  if (b.note) pack.note = String(b.note);
  return Object.keys(pack).length ? pack : null;
}

function ok(body, type) {
  return { status: 200, body, type };
}
function err(status, message, extra = {}) {
  return { status, body: { error: message, ...extra } };
}

/**
 * @param {{ method: string, pathname: string, query?: URLSearchParams, body?: object }} req
 */
export async function routeApi(req) {
  const method = (req.method || "GET").toUpperCase();
  let pathname = req.pathname || "/";
  // Normalize Netlify / local prefixes
  pathname = pathname
    .replace(/^\/\.netlify\/functions\/lpros-api/, "")
    .replace(/^\/lpros-command\/api/, "")
    .replace(/^\/api/, "");
  if (!pathname.startsWith("/")) pathname = `/${pathname}`;
  if (pathname === "") pathname = "/";

  const query = req.query || new URLSearchParams();
  const b = req.body || {};

  if (method === "OPTIONS") {
    return { status: 204, body: "", type: "text/plain" };
  }

  if (method === "GET" && (pathname === "/" || pathname === "/health")) {
    const appConfigured = Boolean(ebayConfig.appId && ebayConfig.certId);
    return ok({
      ok: true,
      service: "lpros-command",
      role: "open ZIK+AutoDS control plane",
      runtime: process.env.NETLIFY ? "netlify" : "node",
      auth: authStatus(),
      ebay: {
        appConfigured,
        env: ebayConfig.env,
        hint: appConfigured
          ? null
          : emptyLiveHint({ configured: false }),
      },
        endpoints: [
          "/research/live",
          "/research/watch",
          "/swarm",
          "/orchestrate/deploy",
          "/orchestrate/campaign",
          "/orchestrate/jobs",
          "/orchestrate/jobs/:id/packages",
          "/orchestrate/jobs/:id/promote",
          "/orchestrate/marathon-defaults",
          "/playground",
          "/playground/jobs",
          "/playground/launch",
          "/playground/hive",
          "/playground/hive/run",
          "/playground/browser/fetch",
          "/playground/vm",
          "/skus",
          "/export",
          "/publish",
          "/orders",
          "/rank",
          "/metrics",
          "/filter",
          "/evidence/verify",
          "/auth/status",
        ],
    });
  }

  if (method === "GET" && pathname === "/auth/status") return ok(authStatus());
  if (method === "GET" && pathname === "/providers") return ok(providerMatrix());

  if (method === "GET" && pathname === "/playbook") {
    const md = readFileSync(resolve(__dirname, "../browser/playbooks.md"), "utf8");
    return ok(md, "text/markdown; charset=utf-8");
  }

  if (method === "GET" && pathname === "/outcomes") {
    return ok({ outcomes: readRecentOutcomes(Number(query.get("limit") || 40)) });
  }

  if (method === "POST" && pathname === "/outcomes") {
    if (b.type === "note" || b.type === "pipeline_run") {
      logOutcome(b);
      return ok({ ok: true });
    }
    return ok(
      recordSaleOutcome({
        title: b.title,
        sku: b.sku,
        profitable: b.profitable,
        returned: b.returned,
        net: b.net,
        salePrice: b.salePrice,
        featureSnapshot: b.featureSnapshot,
        note: b.note,
      })
    );
  }

  if (method === "GET" && pathname === "/skus") {
    return ok(listSkus({ status: query.get("status") || undefined }));
  }

  if (method === "GET" && pathname.startsWith("/skus/") && pathname !== "/skus/promote") {
    const sku = decodeURIComponent(pathname.slice("/skus/".length));
    const row = getSku(sku);
    if (!row) return err(404, "not found");
    return ok({ sku: row, package: buildListingPackage(row) });
  }

  if (method === "DELETE" && pathname.startsWith("/skus/")) {
    const sku = decodeURIComponent(pathname.slice("/skus/".length));
    return ok(removeSku(sku));
  }

  if (method === "POST" && pathname === "/skus/promote") {
    const evidence = evidenceFromBody(b.evidence || b);
    const row = promoteCandidate(b.candidate || b, {
      evidence,
      categoryId: b.categoryId,
      quantity: b.quantity,
      costRatio: b.costRatio,
      productCost: b.productCost ?? evidence?.productCost,
      requireHarden: Boolean(evidence),
      sku: b.sku,
      notes: b.notes,
    });
    return ok(row);
  }

  if (method === "POST" && pathname === "/skus/status") {
    return ok(setSkuStatus(b.sku, b.status, b.patch || {}));
  }

  if (method === "POST" && pathname === "/export") {
    const result = exportPackages({
      status: b.status || "ready",
      format: b.format || "both",
    });
    return ok({
      stamp: result.stamp,
      status: result.status,
      count: result.count,
      files: result.files,
      sample: result.packages.slice(0, 3),
      note: process.env.NETLIFY
        ? "On Netlify, export files are written to /tmp (ephemeral). Prefer CSV download or local npm start for durable exports."
        : undefined,
    });
  }

  if (method === "GET" && pathname === "/export/csv") {
    const status = query.get("status") || "ready";
    const result = exportPackages({ status, format: "csv" });
    const csvFile = result.files.find((f) => f.type === "csv");
    const csv = readFileSync(csvFile.path, "utf8");
    return ok(csv, "text/csv; charset=utf-8");
  }

  if (method === "POST" && pathname === "/publish") {
    return ok(await publishSku(b.sku, { live: Boolean(b.live) }));
  }

  if (method === "POST" && pathname === "/publish/dry-run") {
    return ok(dryRunPublish(b.sku));
  }

  if (method === "GET" && pathname === "/orders") {
    return ok(listOrders({ status: query.get("status") || undefined }));
  }

  if (method === "POST" && pathname === "/orders/ingest") {
    return ok(ingestOrder(b.order || b, b.policy || {}));
  }

  if (method === "POST" && pathname === "/orders/tracking") {
    return ok(
      attachTracking(b.orderId, {
        trackingNumber: b.trackingNumber,
        carrier: b.carrier,
        shippedAt: b.shippedAt,
      })
    );
  }

  if (method === "POST" && pathname === "/orders/push-tracking") {
    return ok(await pushTracking(b.orderId, { live: Boolean(b.live) }));
  }

  if (method === "POST" && pathname === "/orders/pull") {
    return ok(await pullOrders({ limit: b.limit || 20, live: Boolean(b.live) }));
  }

  if (method === "POST" && pathname === "/econ") {
    return ok(
      netProfitPerSale({
        salePrice: Number(b.price),
        productCost: Number(b.cost),
        returnsBufferRate: b.returns ?? 0.04,
        hasStore: Boolean(b.store),
      })
    );
  }

  if (method === "POST" && pathname === "/forecast") {
    const listings = Number(b.listings ?? 300);
    const str = Number(b.str ?? 0.015);
    const avgNet = Number(b.net ?? 9);
    const target = Number(b.target ?? 50);
    return ok({
      expected: expectedDailyProfit({ listings, str, avgNet }),
      needed: listingsNeeded({ targetDailyProfit: target, str, avgNet }),
      stress: stressForecast({ listings, str, avgNet, targetDailyProfit: target }),
    });
  }

  if (method === "POST" && pathname === "/intel") {
    const intel = await competitorIntel({
      q: b.q,
      categoryId: b.categoryId,
      minPrice: Number(b.minPrice ?? 35),
      maxPrice: Number(b.maxPrice ?? 200),
      limit: Number(b.limit ?? 100),
      productCostRatio: Number(b.costRatio ?? 0.4),
    });
    const desk = deskFromResearch(intel, { query: b.q, categoryId: b.categoryId });
    return ok({ ...intel, ...desk, products: desk.products });
  }

  if (method === "POST" && pathname === "/research/live") {
    const appConfigured = Boolean(ebayConfig.appId && ebayConfig.certId);
    if (!appConfigured) {
      return err(503, emptyLiveHint({ configured: false }), { code: "EBAY_CONFIG" });
    }
    const onNetlify = Boolean(process.env.NETLIFY);
    const limit = onNetlify ? Math.min(Number(b.limit ?? 40), 40) : Number(b.limit ?? 80);
    const detailCount = onNetlify ? Math.min(Number(b.detailCount ?? 8), 8) : Number(b.detailCount ?? 12);
    const intel = await competitorIntel({
      q: b.q || "solid wood desk organizer",
      categoryId: b.categoryId,
      minPrice: Number(b.minPrice ?? 35),
      maxPrice: Number(b.maxPrice ?? 200),
      limit,
      productCostRatio: Number(b.costRatio ?? 0.4),
    });
    const seed = (intel.lethalCandidates?.length ? intel.lethalCandidates : intel.items || []).slice(
      0,
      detailCount
    );
    let detailed = seed;
    if (b.details !== false && seed.length) {
      detailed = await enrichItemsWithDetails(seed, { max: detailCount, delayMs: onNetlify ? 120 : 180 });
    }
    const desk = deskFromResearch(
      { ...intel, items: detailed, products: detailed, lethalCandidates: intel.lethalCandidates },
      { query: b.q, categoryId: b.categoryId, configured: true }
    );
    if (!desk.productCount) {
      return err(422, desk.emptyReason || emptyLiveHint(), { code: "NO_LIVE_PRODUCTS", market: intel.market });
    }
    return ok({
      ...intel,
      ...desk,
      products: desk.products,
      lethalCandidates: intel.lethalCandidates,
      detailsFetched: detailed.filter((d) => d.detailFetched).length,
    });
  }

  if (method === "GET" && pathname === "/research/watch") {
    return ok({ sessions: listWatches(20) });
  }
  if (method === "POST" && pathname === "/research/watch") {
    try {
      const session = createWatchSession(b);
      await tickWatch(session.id, { n: 1 });
      return ok(slimWatch(getWatch(session.id)));
    } catch (e) {
      return err(e.status || 500, e.message, { code: e.code });
    }
  }
  if (method === "GET" && pathname.match(/^\/research\/watch\/[^/]+$/)) {
    const id = decodeURIComponent(pathname.split("/").pop());
    const session = getWatch(id);
    if (!session) return err(404, "watch session not found");
    return ok(slimWatch(session));
  }
  if (method === "GET" && pathname.match(/^\/research\/watch\/[^/]+\/events$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const session = getWatch(id);
    if (!session) return err(404, "watch session not found");
    const after = Number(query.get("after") || 0);
    const events = (session.events || []).slice(after);
    return ok({
      events,
      nextIndex: (session.events || []).length,
      status: session.status,
      phase: session.phase,
      progress: session.progress,
      productCount: (session.products || []).length,
    });
  }
  if (method === "POST" && pathname.match(/^\/research\/watch\/[^/]+\/tick$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    try {
      const session = await tickWatch(id, { n: Number(b.n ?? 1) });
      return ok(slimWatch(session));
    } catch (e) {
      return err(e.status || 500, e.message, { code: e.code });
    }
  }
  if (method === "POST" && pathname.match(/^\/research\/watch\/[^/]+\/cancel$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const session = cancelWatch(id);
    if (!session) return err(404, "watch session not found");
    return ok(slimWatch(session));
  }

  if (method === "POST" && pathname === "/rank") {
    const candidates = Array.isArray(b.candidates) ? b.candidates : [];
    if (!candidates.length) return err(400, "candidates[] required");
    const ranked = rankMarket(candidates, {
      minPrice: Number(b.minPrice ?? 35),
      maxPrice: Number(b.maxPrice ?? 200),
      costRatio: Number(b.costRatio ?? 0.4),
      weights: b.weights,
    });
    return ok(ranked);
  }

  if (method === "POST" && pathname === "/metrics") {
    return ok(computeMarketMetrics(b));
  }

  if (method === "POST" && pathname === "/filter") {
    const candidates = Array.isArray(b.candidates) ? b.candidates : [];
    return ok(applyFilters(candidates, b.policy || b));
  }

  if (method === "POST" && pathname === "/evidence/verify") {
    const pack = evidenceFromBody(b.evidence || b);
    if (!pack) return err(400, "evidence pack required");
    const candidate = b.candidate || {
      title: b.title || "candidate",
      salePrice: Number(b.salePrice ?? b.avgSoldPrice ?? 49),
      productCost: Number(b.productCost ?? pack.productCost ?? 20),
      productCostEstimated: pack.productCost == null,
      leadTimeDays: pack.leadTimeDays ?? 7,
      soldEvidenceMissing: true,
      evidenceStatus: "partial",
      demandSources: ["ebay_browse"],
      activeCount: Number(b.activeCount ?? 40),
      density: Number(b.density ?? 40),
      perceivedValue: Number(b.perceivedValue ?? 0.55),
      remorseRisk: Number(b.remorseRisk ?? 0.3),
      scammy: false,
      hasImages: true,
      hasItemSpecifics: true,
      str: Number(b.str ?? 0.015),
    };
    return ok(
      hardenCandidate(candidate, pack, {
        minSalePrice: Number(b.minPrice ?? 35),
        maxSalePrice: Number(b.maxPrice ?? 200),
      })
    );
  }

  if (method === "POST" && pathname === "/listing/draft") {
    return ok(draftListing(b.candidate || b, { brand: b.brand, type: b.type }));
  }

  if (method === "POST" && pathname === "/swarm") {
    const evidencePack = evidenceFromBody(b.evidence || b.evidencePack);
    const data = await runResearchSwarm({
      q: b.q || "desk organizer wood",
      categoryId: b.categoryId || "25339",
      categoryLabel: b.categoryLabel || "Home",
      minPrice: Number(b.minPrice ?? 35),
      maxPrice: Number(b.maxPrice ?? 200),
      costRatio: Number(b.costRatio ?? 0.4),
      crawlPages: Number(b.crawlPages ?? 2),
      deepCrawl: Boolean(b.deepCrawl),
      targetDailyProfit: Number(b.targetDailyProfit ?? 50),
      assumedStr: Number(b.assumedStr ?? 0.015),
      evidencePack,
      draftListings: b.draftListings !== false,
    });

    let promoted = [];
    if (b.promotePass || b.autoPromote) {
      promoted = (data.lethalBoard || [])
        .filter((r) => r.decision === "PASS")
        .slice(0, Number(b.promoteLimit || 5))
        .map((r) =>
          promoteCandidate(r, {
            evidence: evidencePack,
            categoryId: b.categoryId || "25339",
            costRatio: Number(b.costRatio ?? 0.4),
            productCost: evidencePack?.productCost,
            requireHarden: false,
          })
        );
    }
    const desk = deskFromResearch(data, { query: b.q, categoryId: b.categoryId });
    if (!desk.productCount) {
      return err(422, desk.emptyReason || emptyLiveHint(), { code: "NO_LIVE_PRODUCTS", brief: data.brief });
    }
    return ok({ ...data, ...desk, products: desk.products, promoted });
  }

  // ── Agent orchestration: deploy → research → title swarm → spreadsheet ──
  if (method === "POST" && pathname === "/orchestrate/deploy") {
    const onNetlify = Boolean(process.env.NETLIFY);
    const wantsMarathon =
      b.mode === "marathon" ||
      b.marathon === true ||
      (Array.isArray(b.categories) && b.categories.length > 1);
    if (wantsMarathon) {
      if (onNetlify && !b.dryRun) {
        return err(400, "Marathon campaigns need local :8790 (Netlify timeout). Use dryRun:true for a short preview or run locally.");
      }
      const sync = b.sync === true;
      const jobOrPromise = deployCampaign(
        {
          ...b,
          mode: "marathon",
          q: b.q || b.query,
          categories: b.categories,
        },
        { sync }
      );
      const job = sync ? await jobOrPromise : jobOrPromise;
      return ok({
        jobId: job.id,
        type: "campaign",
        status: job.status,
        progress: job.progress,
        sync,
        categoryCount: job.config?.categories?.length,
        note: "Marathon async — poll /orchestrate/jobs/:id/events (long run)",
        error: job.error || undefined,
      });
    }
    const sync = b.sync === true || (onNetlify && b.sync !== false);
    const config = {
      q: b.q || b.query,
      query: b.query || b.q,
      categoryId: b.categoryId,
      category: b.category || b.categoryLabel || "Home",
      cost: b.cost ?? b.productCost,
      altCost: b.altCost ?? b.altProductCost,
      minPrice: b.minPrice,
      maxPrice: b.maxPrice,
      suggestedPrice: b.suggestedPrice,
      variantCount: onNetlify ? Math.min(Number(b.variantCount ?? 120), 150) : b.variantCount ?? 200,
      liveProbeCount: onNetlify ? Math.min(Number(b.liveProbeCount ?? 3), 5) : b.liveProbeCount ?? 12,
      sheetRows: b.sheetRows ?? 150,
      seedQueries: b.seedQueries,
      crawlPages: onNetlify ? 1 : b.crawlPages ?? 1,
      crawlLimit: onNetlify ? 40 : b.crawlLimit,
      detailCount: onNetlify ? Math.min(Number(b.detailCount ?? 5), 6) : b.detailCount ?? 12,
      dryRun: Boolean(b.dryRun),
    };
    const jobOrPromise = deployMission(config, { sync });
    const job = sync ? await jobOrPromise : jobOrPromise;
    return ok({
      jobId: job.id,
      status: job.status,
      progress: job.progress,
      sync,
      note: sync
        ? "Ran synchronously. Download workbook CSV via /orchestrate/jobs/:id/spreadsheet?workbook=1"
        : "Deployed async — poll /orchestrate/jobs/:id/events for live log",
      error: job.error || undefined,
      researched: job.results?.researched,
      productCount: job.results?.productCount,
      productsWithImages: job.results?.productsWithImages,
      recommendations: job.results?.recommendations,
      gallery: job.results?.gallery?.slice(0, 8),
      variantCount: job.results?.variants?.length,
    });
  }

  if (method === "POST" && pathname === "/orchestrate/campaign") {
    const onNetlify = Boolean(process.env.NETLIFY);
    if (onNetlify && !b.dryRun) {
      return err(
        400,
        "Marathon campaigns require local Command (:8790) or CLI — Netlify functions time out. Pass dryRun:true for a preview."
      );
    }
    const sync = Boolean(b.sync);
    const jobOrPromise = deployCampaign(
      {
        mode: "marathon",
        q: b.q || b.query,
        categories: b.categories,
        cost: b.cost,
        minPrice: b.minPrice,
        maxPrice: b.maxPrice,
        suggestedPrice: b.suggestedPrice,
        variantCount: b.variantCount ?? 250,
        detailCount: b.detailCount ?? 30,
        crawlPages: b.crawlPages ?? 4,
        crawlLimit: b.crawlLimit ?? 600,
        intelLimit: b.intelLimit ?? 120,
        liveProbeCount: b.liveProbeCount ?? 10,
        ideasTarget: b.ideasTarget ?? 250,
        dryRun: Boolean(b.dryRun),
      },
      { sync }
    );
    const job = sync ? await jobOrPromise : jobOrPromise;
    return ok({
      jobId: job.id,
      type: "campaign",
      status: job.status,
      progress: job.progress,
      sync,
      categories: job.config?.categories?.map((c) => ({ id: c.categoryId, label: c.label })),
      note: "Long marathon — leave local server running; download ?workbook=1 when done",
      error: job.error || undefined,
      productCount: job.results?.productCount,
      ideaCount: job.results?.ideaCount,
      variantCount: job.results?.variantTotalGenerated,
    });
  }

  if (method === "GET" && pathname === "/orchestrate/marathon-defaults") {
    return ok({ categories: DEFAULT_MARATHON_CATEGORIES });
  }

  if (method === "GET" && pathname === "/orchestrate/jobs") {
    const merged = [...listCampaignJobs(40), ...listJobs(40)]
      .sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)))
      .slice(0, Number(query.get("limit") || 40));
    return ok({ jobs: merged });
  }

  if (method === "GET" && pathname.match(/^\/orchestrate\/jobs\/[^/]+$/)) {
    const jobId = decodeURIComponent(pathname.split("/").pop());
    const job = getJob(jobId) || getCampaignJob(jobId);
    if (!job) return err(404, "job not found");
    const slim = {
      id: job.id,
      type: job.type || (String(job.id).startsWith("camp_") ? "campaign" : "mission"),
      status: job.status,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt,
      config: job.config,
      progress: job.progress,
      error: job.error,
      checkpoints: job.checkpoints?.slice(-10),
      events: job.events?.slice(-100),
      results: job.results
        ? {
            mode: job.results.mode,
            researched: job.results.researched,
            categoryCount: job.results.categoryCount,
            productCount: job.results.productCount,
            productsWithImages: job.results.productsWithImages,
            productsWithUrls: job.results.productsWithUrls,
            productsWithDetail: job.results.productsWithDetail,
            variantTotalGenerated: job.results.variantTotalGenerated,
            ideaCount: job.results.ideaCount,
            narrowedCategory: job.results.narrowedCategory,
            patterns: job.results.patterns,
            pipelineSummary: job.results.pipelineSummary,
            recommendations: job.results.recommendations,
            intel: job.results.intel,
            lanes: job.results.lanes,
            trends: job.results.trends,
            gallery: job.results.gallery,
            packagesPreview: (job.results.packages || []).slice(0, 24),
            packageCount: job.results.packageCount,
            clusters: job.results.clusters,
            imageStats: job.results.imageStats,
            productsPreview: (job.results.products || []).slice(0, 80),
            variantsPreview: (job.results.variants || []).slice(0, 40),
            ideasPreview: job.results.trends?.ideasPreview || job.results.recommendations?.topIdeas,
            columns: job.results.columns,
          }
        : null,
    };
    return ok(slim);
  }

  if (method === "GET" && pathname.match(/^\/orchestrate\/jobs\/[^/]+\/events$/)) {
    const parts = pathname.split("/");
    const jobId = decodeURIComponent(parts[parts.length - 2]);
    const after = Number(query.get("after") || 0);
    const data = getJobEvents(jobId, after) || getCampaignEvents(jobId, after);
    if (!data) return err(404, "job not found");
    return ok(data);
  }

  if (method === "GET" && pathname.match(/^\/orchestrate\/jobs\/[^/]+\/spreadsheet$/)) {
    const parts = pathname.split("/");
    const jobId = decodeURIComponent(parts[parts.length - 2]);
    const opts = {
      workbook: query.get("workbook") === "1" || query.get("workbook") === "true",
      products: query.get("products") === "1" || query.get("products") === "true",
      trends: query.get("trends") === "1" || query.get("trends") === "true",
      ideas: query.get("ideas") === "1" || query.get("ideas") === "true",
      packages: query.get("packages") === "1" || query.get("packages") === "true",
    };
    const sheet =
      getCampaignSpreadsheet(jobId, opts) ||
      getJobSpreadsheet(jobId, { workbook: opts.workbook, products: opts.products });
    if (!sheet) return err(404, "job not found");
    if (query.get("format") === "json") return ok(sheet);
    if (!sheet.ready) {
      return err(409, "spreadsheet not ready", { status: sheet.status, ready: false });
    }
    return ok(sheet.csv, "text/csv; charset=utf-8");
  }

  if (method === "POST" && pathname.match(/^\/orchestrate\/jobs\/[^/]+\/packages$/)) {
    const jobId = decodeURIComponent(pathname.split("/")[3] || pathname.split("/").slice(-2)[0]);
    const job = getJob(jobId) || getCampaignJob(jobId);
    if (!job) return err(404, "job not found");
    try {
      const factory = assemblePackages(job, { maxPackages: Number(b.maxPackages || 25) });
      return ok({
        jobId,
        packageCount: factory.packageCount,
        clusters: factory.clusters,
        imageStats: factory.imageStats,
        packages: factory.packages,
      });
    } catch (e) {
      return err(e.status || 500, e.message);
    }
  }

  if (method === "GET" && pathname.match(/^\/orchestrate\/jobs\/[^/]+\/packages$/)) {
    const jobId = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const job = getJob(jobId) || getCampaignJob(jobId);
    if (!job) return err(404, "job not found");
    if (!job.results?.packages) {
      try {
        assemblePackages(job, { maxPackages: 25 });
      } catch (e) {
        return err(e.status || 409, e.message);
      }
    }
    return ok({
      jobId,
      packageCount: job.results.packageCount,
      clusters: job.results.clusters,
      imageStats: job.results.imageStats,
      packages: job.results.packages,
    });
  }

  if (method === "POST" && pathname.match(/^\/orchestrate\/jobs\/[^/]+\/promote$/)) {
    const jobId = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const job = getJob(jobId) || getCampaignJob(jobId);
    if (!job) return err(404, "job not found");
    try {
      const out = promotePackages(job, {
        limit: Number(b.limit || 8),
        decision: b.decision || "TEST_NOW",
      });
      return ok(out);
    } catch (e) {
      return err(e.status || 500, e.message);
    }
  }

  if (method === "POST" && pathname.match(/^\/orchestrate\/jobs\/[^/]+\/cancel$/)) {
    const jobId = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const job = cancelCampaign(jobId) || requestCancel(jobId);
    if (!job) return err(404, "job not found");
    return ok({ jobId, cancelRequested: true, status: job.status });
  }

  if (method === "POST" && pathname.match(/^\/orchestrate\/jobs\/[^/]+\/resume$/)) {
    const jobId = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const job = resumeCampaign(jobId, { sync: Boolean(b.sync) });
    if (!job) return err(404, "job not found");
    return ok({ jobId, status: job.status, progress: job.progress, note: "Resume async — poll events" });
  }

  if (method === "POST" && pathname === "/fulfill/decide") {
    return ok(fulfillDecision(b.order || b, b.policy || {}));
  }

  // ── Agent playground: job board, sub-agent launcher, browser, VM ──
  if (method === "GET" && pathname === "/playground") {
    return ok({
      ok: true,
      service: "lpros-playground",
      catalog: { agents: AGENT_CATALOG.length, playbooks: PLAYBOOKS.length, recipes: VM_RECIPES.length },
      board: boardSummary(),
      vm: vmSnapshot(),
    });
  }
  if (method === "GET" && pathname === "/playground/catalog") {
    return ok({
      agents: AGENT_CATALOG,
      playbooks: PLAYBOOKS,
      recipes: VM_RECIPES,
      presets: PRESETS,
      packs: listPacks(),
      workloads: WORKLOADS,
    });
  }
  if (method === "GET" && pathname === "/playground/packs") {
    return ok({ packs: listPacks() });
  }
  if (method === "GET" && pathname === "/playground/hive") {
    return ok({
      ok: true,
      workloads: WORKLOADS,
      comms: listComms(40),
      note: "TASK CONTRACTs + specialist workers. Pack-only is not Browse. HOLD default.",
    });
  }
  if (method === "GET" && pathname === "/playground/hive/comms") {
    return ok({ comms: listComms(Number(query.get("limit") || 80)) });
  }
  if (method === "POST" && pathname === "/playground/hive/run") {
    const id = b.workload || b.id || "specialist-gauntlet";
    const out = await runWorkload(id, b.input || b);
    return ok(out);
  }
  if (method === "POST" && pathname === "/playground/hive/condition") {
    return ok(runConditioner(b.input || b));
  }
  if (method === "GET" && pathname === "/playground/board") {
    return ok(boardSummary());
  }
  if (method === "GET" && pathname === "/playground/jobs") {
    const jobs = listPlaygroundJobs({
      status: query.get("status") || undefined,
      agent: query.get("agent") || undefined,
      kind: query.get("kind") || undefined,
      limit: Number(query.get("limit") || 80),
    });
    return ok({ jobs: jobs.map(slimJob), summary: boardSummary() });
  }
  if (method === "POST" && pathname === "/playground/jobs") {
    const job = createJob({
      kind: b.kind || (b.agent === "browser" ? "browser" : b.agent === "vm" ? "vm" : "agent"),
      agent: b.agent || null,
      title: b.title,
      priority: b.priority || "P1",
      parentId: b.parentId || null,
      input: b.input || b,
    });
    if (b.start) {
      const ran = await startJob(job.id, { sync: b.sync !== false });
      return ok({ job: slimJob(ran), result: ran.result, status: ran.status });
    }
    return ok({ job: slimJob(job) });
  }
  if (method === "POST" && pathname === "/playground/launch") {
    const job = await launchAgent({
      agent: b.agent,
      input: b.input || b,
      spawn: b.spawn,
      priority: b.priority || "P1",
      title: b.title,
      sync: b.sync !== false,
      dryRun: Boolean(b.dryRun),
    });
    const kids = (job.children || []).map((id) => getPlaygroundJob(id)).filter(Boolean);
    const market = deskFromPlaygroundJobs([job, ...kids], { query: job.input?.q });
    return ok({
      jobId: job.id,
      status: job.status,
      agent: job.agent,
      children: job.children,
      result: job.result,
      error: job.error,
      brief: job.result?.brief || null,
      market,
      products: market.products,
      productCount: market.productCount,
      emptyReason: market.emptyReason,
      dryRun: market.dryRun,
    });
  }
  if (method === "GET" && pathname.match(/^\/playground\/jobs\/[^/]+$/)) {
    const job = getPlaygroundJob(decodeURIComponent(pathname.split("/").pop()));
    if (!job) return err(404, "job not found");
    return ok(job);
  }
  if (method === "GET" && pathname.match(/^\/playground\/jobs\/[^/]+\/events$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const job = getPlaygroundJob(id);
    if (!job) return err(404, "job not found");
    const after = Number(query.get("after") || 0);
    const events = (job.events || []).slice(after);
    return ok({ events, nextIndex: (job.events || []).length, status: job.status, progress: job.progress });
  }
  if (method === "POST" && pathname.match(/^\/playground\/jobs\/[^/]+\/start$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const job = await startJob(id, { sync: b.sync !== false });
    if (!job) return err(404, "job not found");
    return ok({ job: slimJob(job), result: job.result, status: job.status });
  }
  if (method === "POST" && pathname.match(/^\/playground\/jobs\/[^/]+\/cancel$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const job = cancelJob(id);
    if (!job) return err(404, "job not found");
    return ok({ job: slimJob(job) });
  }
  if (method === "POST" && pathname.match(/^\/playground\/jobs\/[^/]+\/retry$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const job = await retryJob(id, { sync: b.sync !== false });
    if (!job) return err(404, "job not found");
    return ok({ job: slimJob(job), result: job.result, status: job.status });
  }
  if (method === "POST" && pathname.match(/^\/playground\/jobs\/[^/]+\/status$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    try {
      const job = setJobStatus(id, b.status);
      if (!job) return err(404, "job not found");
      return ok({ job: slimJob(job) });
    } catch (e) {
      return err(e.status || 400, e.message);
    }
  }
  if (method === "GET" && pathname === "/playground/browser/sessions") {
    return ok({ sessions: listSessions(40) });
  }
  if (method === "POST" && pathname === "/playground/browser/sessions") {
    return ok({ session: createSession(b) });
  }
  if (method === "GET" && pathname.match(/^\/playground\/browser\/sessions\/[^/]+$/)) {
    const session = getSession(decodeURIComponent(pathname.split("/").pop()));
    if (!session) return err(404, "session not found");
    return ok({ session });
  }
  if (method === "POST" && pathname.match(/^\/playground\/browser\/sessions\/[^/]+\/advance$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const session = advanceSession(id, { capture: b.capture });
    if (!session) return err(404, "session not found");
    return ok({ session });
  }
  if (method === "POST" && pathname.match(/^\/playground\/browser\/sessions\/[^/]+\/capture$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const session = addCapture(id, b);
    if (!session) return err(404, "session not found");
    return ok({ session });
  }
  if (method === "POST" && pathname === "/playground/browser/fetch") {
    try {
      const snapshot = await fetchAllowed(b.url || b.itemId);
      if (b.sessionId) {
        const session = getSession(b.sessionId);
        if (session) {
          session.snapshots.push({ at: new Date().toISOString(), ...snapshot });
          session.url = snapshot.url || session.url;
          session.updatedAt = new Date().toISOString();
          persist("browser", session);
        }
      }
      return ok({ snapshot });
    } catch (e) {
      return err(e.status || 500, e.message);
    }
  }
  if (method === "GET" && pathname === "/playground/vm") {
    return ok(vmSnapshot());
  }
  if (method === "GET" && pathname === "/playground/vm/runs") {
    return ok({ runs: listKind("vm", 40) });
  }
  if (method === "POST" && pathname === "/playground/vm/exec") {
    try {
      const run = await runRecipe(b.recipe || "env", b);
      return ok({ run });
    } catch (e) {
      return err(e.status || 500, e.message);
    }
  }
  if (method === "GET" && pathname === "/playground/activity") {
    return ok({ events: activityFeed(Number(query.get("limit") || 50)) });
  }
  if (method === "GET" && pathname.match(/^\/playground\/jobs\/[^/]+\/tree$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    const tree = jobTree(id);
    if (!tree) return err(404, "job not found");
    return ok(tree);
  }
  if (method === "POST" && pathname.match(/^\/playground\/jobs\/[^/]+\/comment$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    try {
      const job = commentJob(id, b.text || b.comment || b.message);
      if (!job) return err(404, "job not found");
      return ok({ job: slimJob(job) });
    } catch (e) {
      return err(e.status || 400, e.message);
    }
  }
  if (method === "POST" && pathname.match(/^\/playground\/jobs\/[^/]+\/promote$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    try {
      const out = promoteFromJob(id);
      if (!out) return err(404, "job not found");
      return ok(out);
    } catch (e) {
      return err(e.status || 400, e.message, { verdict: e.verdict });
    }
  }
  if (method === "POST" && pathname.match(/^\/playground\/browser\/sessions\/[^/]+\/apply$/)) {
    const id = decodeURIComponent(pathname.split("/").slice(-2)[0]);
    try {
      const out = await applySessionEvidence(id, {
        q: b.q,
        title: b.title,
        salePrice: b.salePrice,
        sync: b.sync !== false,
        relaunchBrain: b.relaunchBrain !== false,
      });
      return ok(out);
    } catch (e) {
      return err(e.status || 500, e.message);
    }
  }

  return err(404, `not found: ${method} ${pathname}`);
}

export function corsHeaders(type = "application/json; charset=utf-8") {
  return {
    "Content-Type": type,
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS,DELETE",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}
