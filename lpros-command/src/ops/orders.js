/**
 * Order intake + fulfill ops — works with manual/CSV import today;
 * Sell Fulfillment API when user refresh token is present.
 */
import { fulfillDecision } from "../fulfill/adapter.js";
import { readJson, writeJson, appendJsonl } from "./store.js";
import { getSku } from "./skus.js";

const FILE = "orders.json";

function empty() {
  return { version: 1, updatedAt: null, orders: [] };
}

export function listOrders({ status } = {}) {
  const db = readJson(FILE, empty);
  let rows = db.orders || [];
  if (status) rows = rows.filter((o) => o.status === status);
  return { updatedAt: db.updatedAt, count: rows.length, orders: rows };
}

export function getOrder(orderId) {
  return (readJson(FILE, empty).orders || []).find((o) => o.orderId === orderId) || null;
}

export function upsertOrder(order) {
  const db = readJson(FILE, empty);
  const orderId = String(order.orderId || `MANUAL-${Date.now()}`);
  const idx = db.orders.findIndex((o) => o.orderId === orderId);
  const now = new Date().toISOString();
  const row = {
    ...(idx >= 0 ? db.orders[idx] : {}),
    ...order,
    orderId,
    updatedAt: now,
    createdAt: idx >= 0 ? db.orders[idx].createdAt : now,
  };
  if (idx >= 0) db.orders[idx] = row;
  else db.orders.unshift(row);
  db.updatedAt = now;
  writeJson(FILE, db);
  appendJsonl("order-events.jsonl", { type: "upsert", orderId, status: row.status });
  return row;
}

/**
 * Import a seller order (manual paste or API shape) and run HOLD/AUTO gate.
 * Looks up SKU registry for cost/margin when line sku matches.
 */
export function ingestOrder(raw = {}, policy = {}) {
  const lineItems = (raw.lineItems || [{ sku: raw.sku, title: raw.title, quantity: 1 }]).map(
    (li) => {
      const reg = li.sku ? getSku(li.sku) : null;
      return {
        sku: li.sku || reg?.sku || null,
        title: li.title || reg?.title || raw.title || null,
        quantity: Number(li.quantity || 1),
        registry: reg
          ? {
              productCost: reg.productCost,
              altProductCost: reg.altProductCost,
              decision: reg.decision,
              status: reg.status,
              net: reg.net,
            }
          : null,
      };
    }
  );

  const primary = lineItems[0];
  const supplierCost =
    raw.supplierCost != null
      ? Number(raw.supplierCost)
      : primary?.registry?.productCost != null
        ? Number(primary.registry.productCost)
        : null;

  const buyerTotal = Number(raw.buyerTotal ?? raw.total ?? raw.salePrice ?? 0);
  const margin =
    supplierCost != null && buyerTotal > 0
      ? (buyerTotal - supplierCost) / buyerTotal
      : raw.margin != null
        ? Number(raw.margin)
        : null;

  const gate = fulfillDecision(
    {
      buyerTotal,
      supplierCost,
      supplierLeadDays: Number(raw.supplierLeadDays ?? raw.leadTimeDays ?? 9),
      margin,
      supplierConfirmed: Boolean(raw.supplierConfirmed),
      policyCompliant: raw.policyCompliant !== false,
      retailArbitrage: Boolean(raw.retailArbitrage),
      lineItems,
    },
    policy
  );

  const status =
    gate.action === "AUTO_FULFILL"
      ? "auto_ok"
      : gate.flags.includes("missing_supplier_cost")
        ? "needs_cost"
        : "hold";

  const order = upsertOrder({
    orderId: raw.orderId,
    source: raw.source || "manual",
    buyerTotal,
    supplierCost,
    margin,
    lineItems,
    shipTo: raw.shipTo || null,
    gate,
    status,
    trackingNumber: raw.trackingNumber || null,
    carrier: raw.carrier || null,
    notes: raw.notes || null,
  });

  return { order, gate };
}

export function attachTracking(orderId, { trackingNumber, carrier, shippedAt } = {}) {
  const row = getOrder(orderId);
  if (!row) throw Object.assign(new Error(`order not found: ${orderId}`), { status: 404 });
  const updated = upsertOrder({
    ...row,
    trackingNumber,
    carrier,
    shippedAt: shippedAt || new Date().toISOString(),
    status: trackingNumber ? "shipped" : row.status,
  });
  appendJsonl("order-events.jsonl", {
    type: "tracking",
    orderId,
    trackingNumber,
    carrier,
  });
  return updated;
}

/** Checklist payload for pushing tracking to eBay (dry-run or live later). */
export function trackingPushPayload(orderId) {
  const row = getOrder(orderId);
  if (!row) throw Object.assign(new Error(`order not found: ${orderId}`), { status: 404 });
  const blockers = [];
  if (!row.trackingNumber) blockers.push("missing trackingNumber");
  if (!row.carrier) blockers.push("missing carrier (e.g. USPS, UPS, FedEx)");
  return {
    orderId: row.orderId,
    ready: blockers.length === 0,
    blockers,
    ebayFulfillment: {
      lineItems: (row.lineItems || []).map((li, i) => ({
        lineItemId: li.lineItemId || String(i + 1),
        quantity: li.quantity || 1,
      })),
      shippedDate: row.shippedAt || new Date().toISOString(),
      shippingCarrierCode: row.carrier,
      trackingNumber: row.trackingNumber,
    },
    checklist: row.gate?.checklist || [],
  };
}
