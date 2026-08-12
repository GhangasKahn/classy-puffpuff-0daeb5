import { createServer } from "node:http";
import { pathToFileURL } from "node:url";
import { config } from "./config.js";
import { buildAltComps } from "./ebay/comps.js";
import { searchActiveListings } from "./ebay/browse.js";
import { searchSoldItems } from "./ebay/insights.js";
import { getAppToken } from "./ebay/client.js";

function send(res, status, body, extraHeaders = {}) {
  const payload = typeof body === "string" ? body : JSON.stringify(body, null, 2);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    ...extraHeaders,
  });
  res.end(payload);
}

function corsHeaders(req) {
  const origin = req.headers.origin || "*";
  const allowed = config.corsOrigins.includes("*") || config.corsOrigins.includes(origin);
  return {
    "Access-Control-Allow-Origin": allowed ? origin === "null" ? "*" : origin : config.corsOrigins[0] || "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
  };
}

function parseUrl(req) {
  return new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);
}

async function handle(req, res) {
  const cors = corsHeaders(req);
  if (req.method === "OPTIONS") {
    res.writeHead(204, cors);
    return res.end();
  }

  const url = parseUrl(req);
  const path = url.pathname.replace(/\/$/, "") || "/";

  try {
    if (req.method === "GET" && (path === "/" || path === "/health")) {
      return send(
        res,
        200,
        {
          ok: true,
          service: "ebay-sold-items",
          env: config.env,
          marketplaceId: config.marketplaceId,
          configured: Boolean(config.appId && config.certId),
          appIdSuffix: config.appId ? config.appId.slice(-12) : null,
        },
        cors
      );
    }

    if (req.method === "GET" && path === "/v1/ebay/token-check") {
      const token = await getAppToken();
      return send(
        res,
        200,
        { ok: true, env: config.env, tokenPreview: `${token.slice(0, 12)}…`, length: token.length },
        cors
      );
    }

    if (req.method === "GET" && path === "/v1/ebay/search") {
      const q = url.searchParams.get("q") || "";
      const limit = url.searchParams.get("limit") || "20";
      const categoryIds = url.searchParams.get("categoryIds") || undefined;
      const data = await searchActiveListings({ q, limit, categoryIds });
      return send(res, 200, data, cors);
    }

    if (req.method === "GET" && path === "/v1/ebay/sold") {
      const q = url.searchParams.get("q") || "";
      const limit = url.searchParams.get("limit") || "20";
      const categoryIds = url.searchParams.get("categoryIds") || undefined;
      try {
        const data = await searchSoldItems({ q, limit, categoryIds });
        return send(res, 200, data, cors);
      } catch (e) {
        return send(
          res,
          e.entitlementLikely ? 403 : e.status || 502,
          {
            error: e.message,
            entitlementLikely: Boolean(e.entitlementLikely),
            listingsNeeded: true,
            evidenceStatus: "listings-needed",
            hint: "Insights is limited-release. Use /v1/ebay/search (Browse) or /v1/market/alt/comps fallback.",
          },
          cors
        );
      }
    }

    // BEDROCK Live / Vault contract
    if (req.method === "GET" && path === "/v1/market/alt/comps") {
      const category = url.searchParams.get("category") || "Watch";
      const ref = url.searchParams.get("ref") || "";
      const categoryIds = url.searchParams.get("categoryIds") || undefined;
      const limit = url.searchParams.get("limit") || "12";
      const data = await buildAltComps({ category, ref, categoryIds, limit });
      return send(res, 200, data, cors);
    }

    // Friendly stubs so the LIVE tab does not hard-fail on other calls
    if (req.method === "GET" && path.startsWith("/v1/market/quote/")) {
      return send(
        res,
        501,
        { error: "quote route not implemented in ebay-sold-items — use bedrock-api for tickers" },
        cors
      );
    }
    if (req.method === "GET" && path === "/v1/market/news") {
      return send(
        res,
        501,
        { error: "news route not implemented in ebay-sold-items", items: [], note: "ebay-sold-items" },
        cors
      );
    }

    return send(res, 404, { error: "not found", path }, cors);
  } catch (e) {
    const status = e.code === "EBAY_CONFIG" ? 503 : e.status || 500;
    return send(
      res,
      status,
      {
        error: e.message || String(e),
        code: e.code || undefined,
        listingsNeeded: true,
        evidenceStatus: "listings-needed",
      },
      cors
    );
  }
}

export function startServer() {
  const server = createServer((req, res) => {
    handle(req, res).catch((e) => {
      send(res, 500, { error: e.message || String(e) }, corsHeaders(req));
    });
  });
  server.listen(config.port, config.host, () => {
    console.log(
      `[ebay-sold-items] ${config.env} listening on http://${config.host}:${config.port}`
    );
    console.log(
      `[ebay-sold-items] configured=${Boolean(config.appId && config.certId)} marketplace=${config.marketplaceId}`
    );
  });
  return server;
}

const isMain =
  process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) startServer();
