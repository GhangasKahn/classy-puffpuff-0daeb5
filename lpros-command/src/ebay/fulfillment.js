/**
 * eBay Fulfillment API helpers — dry-run tracking push; live when user token set.
 */
import { trackingPushPayload, getOrder, upsertOrder } from "../ops/orders.js";
import { appendJsonl } from "../ops/store.js";
import { authStatus, ebaySellFetch, hasUserToken } from "./userToken.js";

export function dryRunTrackingPush(orderId) {
  const payload = trackingPushPayload(orderId);
  return {
    mode: "dry_run",
    ...payload,
    wouldCall: [`POST /sell/fulfillment/v1/order/${orderId}/shipping_fulfillment`],
    auth: authStatus(),
  };
}

export async function pushTracking(orderId, opts = {}) {
  const live = Boolean(opts.live);
  if (!live) return dryRunTrackingPush(orderId);

  if (!hasUserToken()) {
    const err = new Error("live tracking push requires EBAY_USER_REFRESH_TOKEN");
    err.status = 401;
    throw err;
  }

  const payload = trackingPushPayload(orderId);
  if (!payload.ready) {
    const err = new Error(`tracking push blocked: ${payload.blockers.join("; ")}`);
    err.status = 400;
    throw err;
  }

  const res = await ebaySellFetch(
    `/sell/fulfillment/v1/order/${encodeURIComponent(orderId)}/shipping_fulfillment`,
    { method: "POST", body: payload.ebayFulfillment }
  );
  if (!res.ok) {
    const err = new Error(`shipping_fulfillment failed (${res.status})`);
    err.status = res.status;
    err.payload = res.json;
    throw err;
  }

  const row = getOrder(orderId);
  upsertOrder({
    ...row,
    status: "tracking_pushed",
    trackingPushedAt: new Date().toISOString(),
    fulfillmentId: res.json.fulfillmentId || null,
  });
  appendJsonl("order-events.jsonl", { type: "tracking_pushed", orderId });

  return { mode: "live", orderId, status: res.status, json: res.json };
}

/** Pull recent orders when user token present; otherwise explain manual ingest. */
export async function pullOrders({ limit = 20, live = false } = {}) {
  if (!live || !hasUserToken()) {
    return {
      mode: "dry_run",
      message:
        "Set EBAY_USER_REFRESH_TOKEN and call with live:true — or POST /api/orders/ingest with Seller Hub export rows",
      auth: authStatus(),
      wouldCall: ["GET /sell/fulfillment/v1/order?limit=…"],
    };
  }

  const res = await ebaySellFetch("/sell/fulfillment/v1/order", {
    query: { limit: String(limit) },
  });
  if (!res.ok) {
    const err = new Error(`order pull failed (${res.status})`);
    err.status = res.status;
    err.payload = res.json;
    throw err;
  }
  return { mode: "live", orders: res.json.orders || [], raw: res.json };
}
