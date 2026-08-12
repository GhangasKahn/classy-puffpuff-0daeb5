/**
 * LPROS Command — local HTTP desk (Netlify uses netlify/functions/lpros-api.mjs).
 */
import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname, extname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { routeApi, corsHeaders } from "./http/router.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const publicDir = resolve(__dirname, "../public");
const port = Number(process.env.LPROS_COMMAND_PORT || 8790);
const host = process.env.HOST || "127.0.0.1";

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
  res.writeHead(status, corsHeaders(type));
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
  try {
    if (url.pathname.startsWith("/api") || url.pathname === "/api") {
      let body = {};
      if (req.method === "POST" || req.method === "PUT" || req.method === "PATCH") {
        body = await readJson(req);
      }
      const result = await routeApi({
        method: req.method,
        pathname: url.pathname,
        query: url.searchParams,
        body,
      });
      return send(res, result.status, result.body, result.type);
    }
    if (req.method === "GET") return serveStatic(req, res, url);
    return send(res, 404, { error: "not found" });
  } catch (e) {
    console.error(e);
    return send(res, e.status || 500, {
      error: e.message || String(e),
      code: e.code,
      blockers: e.blockers,
      payload: e.payload,
    });
  }
}

const server = createServer((req, res) => {
  handle(req, res);
});
server.listen(port, host, () => {
  console.log(`[lpros-command] http://${host}:${port}`);
});
