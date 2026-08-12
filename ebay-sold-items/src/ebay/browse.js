import { ebayFetch } from "./client.js";

/**
 * Browse API — active listings only.
 * GET /buy/browse/v1/item_summary/search
 */
export async function searchActiveListings({
  q,
  limit = 20,
  categoryIds,
  filter,
  sort,
  minPrice,
  maxPrice,
} = {}) {
  if (!q && !categoryIds) {
    throw new Error("Browse search requires q and/or category_ids");
  }
  const query = {
    limit: String(Math.min(Math.max(Number(limit) || 20, 1), 50)),
  };
  if (q) query.q = q;
  if (categoryIds) query.category_ids = String(categoryIds);
  const filters = [];
  if (filter) filters.push(filter);
  if (minPrice != null || maxPrice != null) {
    const lo = minPrice != null ? Number(minPrice) : 0;
    const hi = maxPrice != null ? Number(maxPrice) : Number.MAX_SAFE_INTEGER;
    filters.push(`price:[${lo}..${hi}]`);
  }
  if (filters.length) query.filter = filters.join(",");
  if (sort) query.sort = sort;

  const { ok, status, json } = await ebayFetch("/buy/browse/v1/item_summary/search", {
    query,
  });

  if (!ok) {
    const err = new Error(
      `Browse search failed (${status}): ${json.errors?.[0]?.message || JSON.stringify(json)}`
    );
    err.status = status;
    err.payload = json;
    throw err;
  }

  const items = (json.itemSummaries || []).map(normalizeBrowseItem);
  return {
    source: "ebay_browse",
    total: json.total ?? items.length,
    items,
    rawHref: json.href,
  };
}

function normalizeBrowseItem(it) {
  const price = it.price?.value != null ? Number(it.price.value) : null;
  return {
    id: it.itemId,
    title: it.title,
    price,
    currency: it.price?.currency || "USD",
    condition: it.condition,
    url: it.itemWebUrl,
    image: it.image?.imageUrl || it.thumbnailImages?.[0]?.imageUrl,
    seller: it.seller?.username,
    buyingOptions: it.buyingOptions,
    itemLocation: it.itemLocation?.country,
    listingDate: null,
    soldDate: null,
    kind: "active",
  };
}
