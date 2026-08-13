import { ebayFetch } from "./client.js";
import { sellerHandle } from "./identity.js";

/**
 * Marketplace Insights API (limited release) — sold items, last ~90 days.
 * GET /buy/marketplace_insights/v1_beta/item_sales/search
 *
 * Many keysets are not entitled. Callers must treat 403/404/409 as
 * listings-needed / sold-unavailable and fall back to Browse actives.
 */
export async function searchSoldItems({
  q,
  categoryIds,
  limit = 20,
  epid,
  gtin,
  filter,
  sort,
} = {}) {
  if (!q && !categoryIds && !epid && !gtin) {
    throw new Error("Sold search requires q, category_ids, epid, or gtin");
  }

  const query = {
    limit: String(Math.min(Math.max(Number(limit) || 20, 1), 50)),
  };
  if (q) query.q = q;
  if (categoryIds) query.category_ids = String(categoryIds);
  if (epid) query.epid = String(epid);
  if (gtin) query.gtin = String(gtin);
  if (filter) query.filter = filter;
  if (sort) query.sort = sort;

  const { ok, status, json } = await ebayFetch(
    "/buy/marketplace_insights/v1_beta/item_sales/search",
    { query }
  );

  if (!ok) {
    const err = new Error(
      `Insights sold search failed (${status}): ${json.errors?.[0]?.message || JSON.stringify(json)}`
    );
    err.status = status;
    err.payload = json;
    err.entitlementLikely = status === 403 || status === 404 || status === 409;
    throw err;
  }

  const sales = json.itemSales || json.itemSummaries || [];
  const items = sales.map(normalizeSale);
  return {
    source: "ebay_marketplace_insights",
    total: json.total ?? items.length,
    items,
    windowDays: 90,
  };
}

function normalizeSale(it) {
  const price =
    it.lastSoldPrice?.value != null
      ? Number(it.lastSoldPrice.value)
      : it.price?.value != null
        ? Number(it.price.value)
        : null;
  return {
    id: it.itemId || it.legacyItemId,
    title: it.title,
    price,
    currency: it.lastSoldPrice?.currency || it.price?.currency || "USD",
    condition: it.condition,
    url: it.itemWebUrl || it.itemHref,
    image: it.image?.imageUrl,
    seller: sellerHandle(it.seller),
    soldDate: it.lastSoldDate || it.soldDate || null,
    buyingOptions: it.buyingOptions,
    kind: "sold",
  };
}
