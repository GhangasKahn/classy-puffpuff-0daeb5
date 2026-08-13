/**
 * Netlify Function — LPROS Command API (CJS entry + dynamic ESM import).
 * Routes: /lpros-command/api/* → this function
 */
const { pathToFileURL } = require("node:url");
const { resolve } = require("node:path");

const root = resolve(__dirname, "../..");

exports.handler = async (event) => {
  try {
    await import(pathToFileURL(resolve(root, "ebay-sold-items/src/config.js")).href);
    const { routeApi, corsHeaders } = await import(
      pathToFileURL(resolve(root, "lpros-command/src/http/router.js")).href
    );

    const method = event.httpMethod || event.requestContext?.http?.method || "GET";
    const rawPath =
      event.path ||
      event.rawPath ||
      event.requestContext?.http?.path ||
      "/";

    let body = {};
    if (event.body) {
      const raw = event.isBase64Encoded
        ? Buffer.from(event.body, "base64").toString("utf8")
        : event.body;
      try {
        body = JSON.parse(raw || "{}");
      } catch {
        body = {};
      }
    }

    const qs = event.queryStringParameters || {};
    const query = new URLSearchParams();
    for (const [k, v] of Object.entries(qs)) {
      if (v != null) query.set(k, String(v));
    }

    const result = await routeApi({
      method,
      pathname: rawPath,
      query,
      body,
    });

    const type = result.type || "application/json; charset=utf-8";
    const payload =
      typeof result.body === "string" ? result.body : JSON.stringify(result.body, null, 2);

    return {
      statusCode: result.status,
      headers: corsHeaders(type),
      body: payload,
    };
  } catch (e) {
    console.error(e);
    return {
      statusCode: e.status || 500,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({
        error: e.message || String(e),
        code: e.code,
      }),
    };
  }
};
