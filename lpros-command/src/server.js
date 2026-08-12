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
      });
    }

    if (req.method === "GET" && url.pathname === "/api/providers") {
      return send(res, 200, providerMatrix());
    }

    if (req.method === "GET" && url.pathname === "/api/playbook") {
      const md = readFileSync(resolve(__dirname, "browser/playbooks.md"), "utf8");
      return send(res, 200, md, "text/markdown; charset=utf-8");
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

    if (req.method === "POST" && url.pathname === "/api/swarm") {
      const b = await readJson(req);
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
