import { ebayFetch } from "./client.js";
import { sellerHandle } from "./identity.js";

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
  fieldgroups = "EXTENDED",
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
  // EXTENDED pulls additionalImages so the desk is not stuck with image-less summaries.
  if (fieldgroups) query.fieldgroups = String(fieldgroups);
  const filters = [];
  if (filter) filters.push(filter);
  if (minPrice != null || maxPrice != null) {
    const lo = minPrice != null ? Number(minPrice) : 0;
    const hi = maxPrice != null ? Number(maxPrice) : Number.MAX_SAFE_INTEGER;
    // eBay Browse requires priceCurrency when using price ranges
    filters.push(`price:[${lo}..${hi}]`, "priceCurrency:USD");
  }
  if (filters.length) query.filter = filters.join(",");
  if (sort) query.sort = sort;

  let { ok, status, json } = await ebayFetch("/buy/browse/v1/item_summary/search", {
    query,
  });

  // Some app tokens reject EXTENDED; never fail closed on images — retry MATCHING_ITEMS.
  if (!ok && query.fieldgroups && query.fieldgroups !== "MATCHING_ITEMS") {
    const retryQuery = { ...query, fieldgroups: "MATCHING_ITEMS" };
    const retry = await ebayFetch("/buy/browse/v1/item_summary/search", { query: retryQuery });
    ok = retry.ok;
    status = retry.status;
    json = retry.json;
  }

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
  const primary = it.image?.imageUrl || null;
  const thumbs = (it.thumbnailImages || []).map((t) => t.imageUrl).filter(Boolean);
  const additional = (it.additionalImages || []).map((t) => t.imageUrl).filter(Boolean);
  const images = [...new Set([primary, ...thumbs, ...additional].filter(Boolean))];
  return {
    id: it.itemId,
    legacyItemId: it.legacyItemId,
    title: it.title,
    price,
    currency: it.price?.currency || "USD",
    condition: it.condition,
    url: it.itemWebUrl,
    image: images[0] || null,
    images,
    thumbnail: thumbs[0] || images[0] || null,
    watchCount: it.watchCount != null ? Number(it.watchCount) : null,
    seller: sellerHandle(it.seller),
    sellerFeedback: it.seller?.feedbackPercentage != null ? Number(it.seller.feedbackPercentage) : null,
    buyingOptions: it.buyingOptions,
    itemLocation: it.itemLocation?.country,
    categories: it.categories,
    leafCategoryIds: it.leafCategoryIds,
    listingDate: it.itemCreationDate || it.listingDate || null,
    soldDate: null,
    kind: "active",
  };
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * Full listing detail — official Browse getItem (description, gallery, specifics).
 * This is the ToS-safe substitute for HTML page scraping.
 * GET /buy/browse/v1/item/{item_id}
 */
export async function getBrowseItem(itemId, { fieldgroups } = {}) {
  if (!itemId) throw new Error("itemId required");
  const id = encodeURIComponent(String(itemId));
  const query = {};
  // PRODUCT for enriched product fields when available
  if (fieldgroups) query.fieldgroups = String(fieldgroups);
  else query.fieldgroups = "PRODUCT";

  const { ok, status, json } = await ebayFetch(`/buy/browse/v1/item/${id}`, { query });
  if (!ok) {
    const err = new Error(
      `Browse getItem failed (${status}): ${json.errors?.[0]?.message || JSON.stringify(json)}`
    );
    err.status = status;
    err.payload = json;
    throw err;
  }
  return normalizeBrowseItemDetail(json);
}

/**
 * Batch fetch details for ranked candidates (rate-limit friendly sequential).
 */
export async function enrichItemsWithDetails(items = [], { max = 12, delayMs = 200 } = {}) {
  const out = [];
  const slice = (items || []).filter((it) => it?.id || it?.itemId).slice(0, max);
  for (const it of slice) {
    try {
      const detail = await getBrowseItem(it.id || it.itemId);
      out.push({
        ...it,
        ...detail,
        // preserve search rank fields
        rank: it.rank,
        rankScore: it.rankScore,
        perceivedValue: it.perceivedValue ?? detail.perceivedValue,
        image: detail.image || it.image,
        images: detail.images?.length ? detail.images : it.images,
        url: detail.url || it.url,
        detailFetched: true,
      });
    } catch (e) {
      out.push({
        ...it,
        detailFetched: false,
        detailError: e.message,
      });
    }
    if (delayMs > 0) await sleep(delayMs);
  }
  return out;
}

function normalizeBrowseItemDetail(it) {
  const base = normalizeBrowseItem(it);
  const descHtml = it.description || it.shortDescription || "";
  const specifics = {};
  for (const g of it.localizedAspects || []) {
    if (g?.name && g?.value != null) specifics[g.name] = g.value;
  }
  // Also common product aspects
  for (const g of it.product?.aspects || []) {
    const name = g?.name || g?.localizedName;
    const vals = g?.values || g?.value;
    if (name && vals != null) specifics[name] = Array.isArray(vals) ? vals.join(", ") : vals;
  }
  const quantity =
    it.estimatedAvailabilities?.[0]?.estimatedAvailableQuantity ??
    it.estimatedAvailabilities?.[0]?.availabilityThreshold ??
    null;

  return {
    ...base,
    descriptionHtml: descHtml,
    descriptionText: stripHtml(descHtml).slice(0, 4000),
    shortDescription: it.shortDescription || null,
    itemSpecifics: specifics,
    brand: it.brand || specifics.Brand || it.product?.brand || null,
    mpn: it.mpn || specifics.MPN || null,
    gtin: it.gtin || null,
    epid: it.epid || it.product?.epid || null,
    categoryPath: (it.categoryPath || "").replace(/\|/g, " > ") || null,
    categoryIdLeaf: it.categoryId || base.leafCategoryIds?.[0] || null,
    imageCount: base.images?.length || 0,
    sellerFeedbackScore:
      it.seller?.feedbackScore != null ? Number(it.seller.feedbackScore) : null,
    quantityAvailable: quantity != null ? Number(quantity) : null,
    shippingOptions: (it.shippingOptions || []).slice(0, 3).map((s) => ({
      type: s.shippingCarrierCode || s.type,
      cost: s.shippingCost?.value != null ? Number(s.shippingCost.value) : null,
      currency: s.shippingCost?.currency,
    })),
    returnTerms: it.returnTerms
      ? {
          returnsAccepted: it.returnTerms.returnsAccepted,
          refundMethod: it.returnTerms.refundMethod,
          returnPeriod: it.returnTerms.returnPeriod,
        }
      : null,
    localizedTitle: it.title,
    rawItemId: it.itemId,
  };
}

function stripHtml(html) {
  return String(html || "")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/\s+/g, " ")
    .trim();
}

export { stripHtml };
