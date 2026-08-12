/**
 * LPROS Command — HTTP desk for research swarm, intel, economics, fulfillment gates.
 */
import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname, extname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { runResearchSwarm } from "./swarm/research.js";
import { competitorIntel } from "./intel/competitor.js";
import { fulfillDecision, providerMatrix } from "./fulfill/adapter.js";
import {
  netProfitPerSale,
  listingsNeeded,
  expectedDailyProfit,
  stressForecast,
} from "../../lpros/src/core/economics.js";
import { hardenCandidate } from "../../lpros/src/core/evidence.js";
import { draftListing } from "../../lpros/src/agents/listing.js";
import {
  readRecentOutcomes,
  recordSaleOutcome,
  logOutcome,
} from "../../lpros/src/agents/outcome.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const publicDir = resolve(__dirname, "../public");
const port = Number(process.env.LPROS_COMMAND_PORT || 8790);
const host = process.env.HOST || "127.0.0.1";

// Load eBay env once
await import(pathToFileURL(resolve(__dirname, "../../ebay-sold-items/src/config.js")).href);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".svg": "image/svg+xml",
};

function send(res, status, body, type = "application/json; charset=utf-8") {
  const payload = typeof body === "string" ? body : JSON.stringify(body, null, 2);
  res.writeHead(status, {
    "Content-Type": type,
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  });
  res.end(payload);
}

function readJson(req) {
  return new Promise((resolveP, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      try {
        const raw = Buffer.concat(chunks).toString("utf8") || "{}";
        resolveP(JSON.parse(raw));
      } catch (e) {
        reject(e);
      }
    });
    req.on("error", reject);
  });
}

function serveStatic(req, res, url) {
  let path = url.pathname === "/" ? "/index.html" : url.pathname;
  if (path.includes("..")) return send(res, 400, { error: "bad path" });
  const file = join(publicDir, path);
  if (!existsSync(file)) return send(res, 404, { error: "not found" });
  const ext = extname(file);
  send(res, 200, readFileSync(file, "utf8"), MIME[ext] || "application/octet-stream");
}

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

async function handle(req, res) {
  const url = new URL(req.url || "/", `http://${req.headers.host}`);
  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    });
    return res.end();
  }

  try {
    if (req.method === "GET" && url.pathname === "/api/health") {
      return send(res, 200, {
        ok: true,
        service: "lpros-command",
        role: "open ZIK+AutoDS control plane",
        port,
        endpoints: [
          "/api/swarm",
          "/api/intel",
          "/api/evidence/verify",
          "/api/listing/draft",
          "/api/outcomes",
          "/api/econ",
          "/api/forecast",
          "/api/fulfill/decide",
          "/api/providers",
          "/api/playbook",
        ],
      });
    }

    if (req.method === "GET" && url.pathname === "/api/providers") {
      return send(res, 200, providerMatrix());
    }

    if (req.method === "GET" && url.pathname === "/api/playbook") {
      const md = readFileSync(resolve(__dirname, "browser/playbooks.md"), "utf8");
      return send(res, 200, md, "text/markdown; charset=utf-8");
    }

    if (req.method === "GET" && url.pathname === "/api/outcomes") {
      const limit = Number(url.searchParams.get("limit") || 40);
      return send(res, 200, { outcomes: readRecentOutcomes(limit) });
    }

    if (req.method === "POST" && url.pathname === "/api/outcomes") {
      const b = await readJson(req);
      if (b.type === "note" || b.type === "pipeline_run") {
        logOutcome(b);
        return send(res, 200, { ok: true });
      }
      const result = recordSaleOutcome({
        title: b.title,
        sku: b.sku,
        profitable: b.profitable,
        returned: b.returned,
        net: b.net,
        salePrice: b.salePrice,
        featureSnapshot: b.featureSnapshot,
        note: b.note,
      });
      return send(res, 200, result);
    }

    if (req.method === "POST" && url.pathname === "/api/econ") {
      const b = await readJson(req);
      return send(
        res,
        200,
        netProfitPerSale({
          salePrice: Number(b.price),
          productCost: Number(b.cost),
          returnsBufferRate: b.returns ?? 0.04,
          hasStore: Boolean(b.store),
        })
      );
    }

    if (req.method === "POST" && url.pathname === "/api/forecast") {
      const b = await readJson(req);
      const listings = Number(b.listings ?? 300);
      const str = Number(b.str ?? 0.015);
      const avgNet = Number(b.net ?? 9);
      const target = Number(b.target ?? 50);
      return send(res, 200, {
        expected: expectedDailyProfit({ listings, str, avgNet }),
        needed: listingsNeeded({ targetDailyProfit: target, str, avgNet }),
        stress: stressForecast({ listings, str, avgNet, targetDailyProfit: target }),
      });
    }

    if (req.method === "POST" && url.pathname === "/api/intel") {
      const b = await readJson(req);
      const data = await competitorIntel({
        q: b.q,
        categoryId: b.categoryId,
        minPrice: Number(b.minPrice ?? 35),
        maxPrice: Number(b.maxPrice ?? 200),
        limit: Number(b.limit ?? 100),
        productCostRatio: Number(b.costRatio ?? 0.4),
      });
      return send(res, 200, data);
    }

    if (req.method === "POST" && url.pathname === "/api/evidence/verify") {
      const b = await readJson(req);
      const pack = evidenceFromBody(b.evidence || b);
      if (!pack) return send(res, 400, { error: "evidence pack required" });
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
      const result = hardenCandidate(candidate, pack, {
        minSalePrice: Number(b.minPrice ?? 35),
        maxSalePrice: Number(b.maxPrice ?? 200),
      });
      return send(res, 200, result);
    }

    if (req.method === "POST" && url.pathname === "/api/listing/draft") {
      const b = await readJson(req);
      const draft = draftListing(b.candidate || b, { brand: b.brand, type: b.type });
      return send(res, 200, draft);
    }

    if (req.method === "POST" && url.pathname === "/api/swarm") {
      const b = await readJson(req);
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
      return send(res, 200, data);
    }

    if (req.method === "POST" && url.pathname === "/api/fulfill/decide") {
      const b = await readJson(req);
      return send(res, 200, fulfillDecision(b.order || b, b.policy || {}));
    }

    if (req.method === "GET") return serveStatic(req, res, url);
    return send(res, 404, { error: "not found" });
  } catch (e) {
    console.error(e);
    return send(res, e.status || 500, { error: e.message || String(e) });
  }
}

const server = createServer((req, res) => {
  handle(req, res);
});
server.listen(port, host, () => {
  console.log(`[lpros-command] http://${host}:${port}`);
});
