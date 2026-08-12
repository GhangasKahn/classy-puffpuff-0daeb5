import { ebayFetch } from "./client.js";

/**
 * Browse API — active listings only.
 * GET /buy/browse/v1/item_summary/search
 *
 * Pagination: limit up to 200, offset, or follow `next` URL from the response.
 * Official API crawl — not HTML scraping (ToS-safe).
 */
export async function searchActiveListings({
  q,
  limit = 20,
  offset = 0,
  categoryIds,
  filter,
  sort,
  minPrice,
  maxPrice,
} = {}) {
  if (!q && !categoryIds) {
    throw new Error("Browse search requires q and/or category_ids");
  }
  const pageSize = Math.min(Math.max(Number(limit) || 20, 1), 200);
  const query = {
    limit: String(pageSize),
    offset: String(Math.max(0, Number(offset) || 0)),
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

  return normalizeSearchPage(json);
}

/** Follow Browse API `next` / absolute search URL (pagination). */
export async function searchActiveListingsByUrl(nextUrl) {
  if (!nextUrl) throw new Error("nextUrl required");
  const { ok, status, json } = await ebayFetch(nextUrl);
  if (!ok) {
    const err = new Error(
      `Browse next-page failed (${status}): ${json.errors?.[0]?.message || JSON.stringify(json)}`
    );
    err.status = status;
    err.payload = json;
    throw err;
  }
  return normalizeSearchPage(json);
}

function normalizeSearchPage(json) {
  const items = (json.itemSummaries || []).map(normalizeBrowseItem);
  return {
    source: "ebay_browse",
    total: json.total ?? items.length,
    limit: json.limit,
    offset: json.offset,
    next: json.next || null,
    prev: json.prev || null,
    items,
    rawHref: json.href,
  };
}

/**
 * Async generator: page through all active items in a category (and optional q).
 * Yields { page, items, total, offset }.
 */
export async function* iterateCategoryListings({
  categoryIds,
  q,
  minPrice,
  maxPrice,
  sort,
  filter,
  pageSize = 200,
  maxPages = 50,
  maxItems = 5000,
  delayMs = 350,
} = {}) {
  if (!categoryIds && !q) throw new Error("categoryIds or q required");
  let page = 0;
  let fetched = 0;
  let nextUrl = null;
  let total = null;

  while (page < maxPages && fetched < maxItems) {
    const res = nextUrl
      ? await searchActiveListingsByUrl(nextUrl)
      : await searchActiveListings({
          categoryIds,
          q,
          minPrice,
          maxPrice,
          sort,
          filter,
          limit: pageSize,
          offset: page * pageSize,
        });

    total = res.total ?? total;
    const items = res.items || [];
    if (!items.length) break;

    fetched += items.length;
    yield {
      page: page + 1,
      offset: res.offset ?? page * pageSize,
      total,
      items,
      fetched,
    };

    page += 1;
    // eBay often caps deep pagination; stop when no next or short page
    if (!res.next || items.length < pageSize) break;
    // Hard stop near API practical ceiling (~10k offset)
    const nextOffset = (res.offset ?? 0) + items.length;
    if (nextOffset >= 10000 || (total != null && nextOffset >= total)) break;

    nextUrl = res.next;
    if (delayMs > 0) await sleep(delayMs);
  }
}

function normalizeBrowseItem(it) {
  const price = it.price?.value != null ? Number(it.price.value) : null;
  return {
    id: it.itemId,
    legacyItemId: it.legacyItemId,
    title: it.title,
    price,
    currency: it.price?.currency || "USD",
    condition: it.condition,
    url: it.itemWebUrl,
    image: it.image?.imageUrl || it.thumbnailImages?.[0]?.imageUrl,
    seller: it.seller?.username,
    buyingOptions: it.buyingOptions,
    itemLocation: it.itemLocation?.country,
    categories: it.categories,
    leafCategoryIds: it.leafCategoryIds,
    listingDate: null,
    soldDate: null,
    kind: "active",
  };
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
