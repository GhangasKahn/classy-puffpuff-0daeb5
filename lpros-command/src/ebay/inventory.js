/**
 * eBay Inventory API — dry-run by default; live when user token + policies set.
 * PUT inventory item → create offer → publish offer
 */
import { buildListingPackage } from "../ops/packages.js";
import { getSku, setSkuStatus } from "../ops/skus.js";
import { appendJsonl } from "../ops/store.js";
import { authStatus, ebaySellFetch, hasUserToken } from "./userToken.js";

export function dryRunPublish(sku, opts = {}) {
  const row = typeof sku === "string" ? getSku(sku) : sku;
  if (!row) throw Object.assign(new Error("SKU not found"), { status: 404 });
  const pkg = buildListingPackage(row, opts);
  const auth = authStatus();
  return {
    mode: "dry_run",
    sku: row.sku,
    wouldCall: [
      `PUT /sell/inventory/v1/inventory_item/${row.sku}`,
      "POST /sell/inventory/v1/offer",
      "POST /sell/inventory/v1/offer/{offerId}/publish",
    ],
    package: pkg,
    auth,
    canGoLive: auth.sellLive && pkg.ready,
    next: pkg.ready
      ? auth.sellLive
        ? "Call publishSku(sku, { live: true })"
        : "Add EBAY_USER_REFRESH_TOKEN + business policies, or import CSV in Seller Hub"
      : "Clear blockers on package (photos, PASS status, policies)",
  };
}

/**
 * @param {string} sku
 * @param {{ live?: boolean }} [opts]
 */
export async function publishSku(sku, opts = {}) {
  const live = Boolean(opts.live);
  if (!live) return dryRunPublish(sku, opts);

  if (!hasUserToken()) {
    const err = new Error("live publish requires EBAY_USER_REFRESH_TOKEN");
    err.status = 401;
    err.code = "EBAY_USER_TOKEN";
    throw err;
  }

  const row = getSku(sku);
  if (!row) throw Object.assign(new Error("SKU not found"), { status: 404 });
  const pkg = buildListingPackage(row, opts);
  if (!pkg.ready) {
    const err = new Error(`publish blocked: ${pkg.blockers.join("; ")}`);
    err.status = 400;
    err.blockers = pkg.blockers;
    throw err;
  }

  const put = await ebaySellFetch(`/sell/inventory/v1/inventory_item/${encodeURIComponent(sku)}`, {
    method: "PUT",
    body: pkg.inventoryItem,
  });
  if (!put.ok) {
    const err = new Error(`inventory_item failed (${put.status})`);
    err.status = put.status;
    err.payload = put.json;
    throw err;
  }

  const offerBody = { ...pkg.offer };
  // Drop null policy ids — API rejects nulls
  for (const k of Object.keys(offerBody.listingPolicies)) {
    if (!offerBody.listingPolicies[k]) delete offerBody.listingPolicies[k];
  }
  if (!offerBody.merchantLocationKey) delete offerBody.merchantLocationKey;

  const offer = await ebaySellFetch("/sell/inventory/v1/offer", {
    method: "POST",
    body: offerBody,
  });
  if (!offer.ok) {
    const err = new Error(`offer create failed (${offer.status})`);
    err.status = offer.status;
    err.payload = offer.json;
    throw err;
  }

  const offerId = offer.json.offerId || offer.json.offerid;
  const pub = await ebaySellFetch(`/sell/inventory/v1/offer/${offerId}/publish`, {
    method: "POST",
  });
  if (!pub.ok) {
    const err = new Error(`offer publish failed (${pub.status})`);
    err.status = pub.status;
    err.payload = pub.json;
    err.offerId = offerId;
    throw err;
  }

  const listingId = pub.json.listingId || pub.json.listingid;
  setSkuStatus(sku, "listed", {
    offerId,
    listingId,
    listedAt: new Date().toISOString(),
  });
  appendJsonl("publish-events.jsonl", {
    type: "publish_live",
    sku,
    offerId,
    listingId,
  });

  return {
    mode: "live",
    sku,
    offerId,
    listingId,
    inventoryStatus: put.status,
    offerStatus: offer.status,
    publishStatus: pub.status,
  };
}
