/**
 * eBay user OAuth (authorization-code refresh) for Sell APIs.
 * Application tokens cannot create listings or pull seller orders.
 *
 * Env:
 *   EBAY_USER_REFRESH_TOKEN  — required for live Sell calls
 *   EBAY_USER_SCOPES         — optional override
 */
import { config, assertEbayConfigured } from "../../../ebay-sold-items/src/config.js";

let cached = { token: null, expiresAt: 0 };

function basicAuthHeader(appId, certId) {
  return "Basic " + Buffer.from(`${appId}:${certId}`, "utf8").toString("base64");
}

export function hasUserToken() {
  return Boolean(process.env.EBAY_USER_REFRESH_TOKEN);
}

export function sellScopes() {
  return (
    process.env.EBAY_USER_SCOPES ||
    [
      "https://api.ebay.com/oauth/api_scope",
      "https://api.ebay.com/oauth/api_scope/sell.inventory",
      "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
      "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
      "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
      "https://api.ebay.com/oauth/api_scope/sell.account",
      "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
    ].join(" ")
  );
}

export async function getUserToken({ force = false } = {}) {
  assertEbayConfigured();
  const refresh = process.env.EBAY_USER_REFRESH_TOKEN;
  if (!refresh) {
    const err = new Error(
      "EBAY_USER_REFRESH_TOKEN missing — Sell Inventory/Fulfillment need a user token. Use dryRun or export CSV for Seller Hub."
    );
    err.code = "EBAY_USER_TOKEN";
    err.status = 401;
    throw err;
  }

  const now = Date.now();
  if (!force && cached.token && now < cached.expiresAt - 60_000) return cached.token;

  const url = `${config.apiRoot}/identity/v1/oauth2/token`;
  const body = new URLSearchParams({
    grant_type: "refresh_token",
    refresh_token: refresh,
    scope: sellScopes(),
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
      `eBay user OAuth failed (${res.status}): ${json.error_description || json.error || text}`
    );
    err.status = res.status;
    err.payload = json;
    throw err;
  }

  const expiresIn = Number(json.expires_in || 7200);
  cached = { token: json.access_token, expiresAt: now + expiresIn * 1000 };
  return cached.token;
}

export async function ebaySellFetch(path, { method = "GET", query, body, headers } = {}) {
  const token = await getUserToken();
  const qs = query ? `?${new URLSearchParams(query)}` : "";
  const url = path.startsWith("http") ? path : `${config.apiRoot}${path}${qs}`;
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
      "Content-Type": "application/json",
      "Content-Language": "en-US",
      "X-EBAY-C-MARKETPLACE-ID": config.marketplaceId,
      ...(headers || {}),
    },
    body: body != null ? JSON.stringify(body) : undefined,
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

export function resetUserTokenCache() {
  cached = { token: null, expiresAt: 0 };
}

export function authStatus() {
  return {
    appConfigured: Boolean(config.appId && config.certId),
    env: config.env,
    marketplaceId: config.marketplaceId,
    userRefreshPresent: hasUserToken(),
    sellLive: hasUserToken(),
    mode: hasUserToken() ? "live_sell_capable" : "export_and_dry_run",
    needsForLivePublish: [
      "EBAY_USER_REFRESH_TOKEN",
      "EBAY_FULFILLMENT_POLICY_ID",
      "EBAY_PAYMENT_POLICY_ID",
      "EBAY_RETURN_POLICY_ID",
      "EBAY_MERCHANT_LOCATION_KEY",
    ].filter((k) => !process.env[k]),
  };
}
