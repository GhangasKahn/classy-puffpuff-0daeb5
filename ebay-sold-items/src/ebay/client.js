import { config, assertEbayConfigured } from "../config.js";

let cached = { token: null, expiresAt: 0 };

function basicAuthHeader(appId, certId) {
  return "Basic " + Buffer.from(`${appId}:${certId}`, "utf8").toString("base64");
}

/**
 * OAuth 2.0 client-credentials grant (application token).
 * https://developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html
 */
export async function getAppToken({ force = false } = {}) {
  assertEbayConfigured();
  const now = Date.now();
  if (!force && cached.token && now < cached.expiresAt - 60_000) {
    return cached.token;
  }

  const url = `${config.apiRoot}/identity/v1/oauth2/token`;
  const body = new URLSearchParams({
    grant_type: "client_credentials",
    scope: config.scope,
  });

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Authorization: basicAuthHeader(config.appId, config.certId),
    },
    body,
  });

  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    json = { raw: text };
  }

  if (!res.ok) {
    const err = new Error(
      `eBay OAuth failed (${res.status}): ${json.error_description || json.error || text}`
    );
    err.status = res.status;
    err.payload = json;
    throw err;
  }

  const expiresIn = Number(json.expires_in || 7200);
  cached = {
    token: json.access_token,
    expiresAt: now + expiresIn * 1000,
  };
  return cached.token;
}

export async function ebayFetch(path, { query, headers } = {}) {
  const token = await getAppToken();
  const qs = query ? `?${new URLSearchParams(query)}` : "";
  const url = path.startsWith("http") ? path : `${config.apiRoot}${path}${qs}`;
  const res = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-EBAY-C-MARKETPLACE-ID": config.marketplaceId,
      ...(headers || {}),
    },
  });
  const text = await res.text();
  let json;
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    json = { raw: text };
  }
  return { ok: res.ok, status: res.status, json, headers: res.headers };
}

export function resetTokenCache() {
  cached = { token: null, expiresAt: 0 };
}
