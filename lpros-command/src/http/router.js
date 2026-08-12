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
import { dryRunPublish, publishSku } from "../ebay/inventory.js";
import { pushTracking, pullOrders } from "../ebay/fulfillment.js";

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
    return ok({
      ok: true,
      service: "lpros-command",
      role: "open ZIK+AutoDS control plane",
      runtime: process.env.NETLIFY ? "netlify" : "node",
      auth: authStatus(),
      endpoints: [
        "/swarm",
        "/skus",
        "/export",
        "/publish",
        "/orders",
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
    return ok(
      await competitorIntel({
        q: b.q,
        categoryId: b.categoryId,
        minPrice: Number(b.minPrice ?? 35),
        maxPrice: Number(b.maxPrice ?? 200),
        limit: Number(b.limit ?? 100),
        productCostRatio: Number(b.costRatio ?? 0.4),
      })
    );
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
    return ok({ ...data, promoted });
  }

  if (method === "POST" && pathname === "/fulfill/decide") {
    return ok(fulfillDecision(b.order || b, b.policy || {}));
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
