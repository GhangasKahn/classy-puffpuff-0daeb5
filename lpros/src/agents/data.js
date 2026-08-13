/** Data Agent — Taxonomy + Browse + comps → raw candidate features */
import { loadEbayEnv } from "./_env.js";
await loadEbayEnv();

import { searchActiveListings } from "../../../ebay-sold-items/src/ebay/browse.js";
import { buildAltComps, resolveCategoryId } from "../../../ebay-sold-items/src/ebay/comps.js";
import { getCategorySubtree, collectLeaves, getDefaultCategoryTreeId } from "../ebay/taxonomy.js";

export async function fetchCategoryLeaves(rootCategoryId) {
  await getDefaultCategoryTreeId();
  const tree = await getCategorySubtree(rootCategoryId);
  const root = tree.categorySubtreeNode || tree.category_subtree_node || tree;
  return collectLeaves(root).slice(0, 80);
}

export async function fetchDemandSnapshot({
  category,
  ref,
  categoryIds,
  limit = 40,
  minPrice = 35,
  maxPrice = 200,
} = {}) {
  const comps = await buildAltComps({ category, ref, categoryIds, limit });
  let browse = null;
  const q = ref || category;
  const cat = categoryIds || resolveCategoryId(category);
  const priceOpts = { minPrice, maxPrice, limit };
  try {
    browse = await searchActiveListings({
      q,
      categoryIds: cat,
      ...priceOpts,
    });
    // Keyword queries often miss when leaf category IDs are wrong — retry unfiltered.
    if ((!browse.items || browse.items.length === 0) && cat) {
      browse = await searchActiveListings({ q, ...priceOpts });
    }
  } catch (e) {
    try {
      browse = await searchActiveListings({ q, ...priceOpts });
    } catch (e2) {
      browse = { error: e2.message, items: [] };
    }
  }
  // Drop anything outside the high-ticket band (API filter is best-effort)
  if (browse?.items?.length) {
    browse = {
      ...browse,
      items: browse.items.filter(
        (i) => i.price != null && i.price >= minPrice && i.price <= maxPrice
      ),
    };
  }
  if (comps.comps?.length) {
    comps.comps = comps.comps.filter(
      (c) => c.price != null && c.price >= minPrice && c.price <= maxPrice
    );
    const bandPrices = comps.comps.map((c) => c.price);
    if (bandPrices.length) {
      const sorted = [...bandPrices].sort((a, b) => a - b);
      comps.suggestedValue = Math.round(sorted[Math.floor(sorted.length / 2)]);
      comps.activeCount = comps.comps.filter((c) => c.kind === "active").length || comps.activeCount;
    } else {
      comps.suggestedValue = null;
    }
  }
  // If comps empty but browse has items, synthesize suggested value from browse
  if ((!comps.comps || comps.comps.length === 0) && browse?.items?.length) {
    const prices = browse.items.map((i) => i.price).filter((p) => p > 0);
    const sorted = [...prices].sort((a, b) => a - b);
    const mid = sorted[Math.floor(sorted.length / 2)];
    comps.comps = browse.items.filter((i) => i.price > 0).map((i) => ({
      source: "eBay active",
      price: i.price,
      date: new Date().toISOString().slice(0, 10),
      grade: i.condition,
      title: i.title,
      url: i.url,
      id: i.id,
      kind: "active",
    }));
    comps.activeCount = browse.total ?? browse.items.length;
    comps.suggestedValue = mid != null ? Math.round(mid) : null;
    comps.evidenceStatus = "partial";
    comps.soldEvidenceMissing = true;
    comps.listingsNeeded = false;
    comps.note = (comps.note || "") + " Comps synthesized from unfiltered Browse fallback.";
  }
  return { comps, browse, priceBand: { minPrice, maxPrice } };
}

export async function buildCandidatesFromQuery({
  category = "Watch",
  queries = [],
  productCostRatio = 0.45,
  leadTimeDays = 7,
  sourcePath = "wholesale_unspecified",
  minPrice = 35,
  maxPrice = 200,
  categoryIds,
} = {}) {
  const qlist = queries.length ? queries : [category];
  const out = [];
  for (const q of qlist) {
    const snap = await fetchDemandSnapshot({
      category,
      ref: q,
      categoryIds,
      minPrice,
      maxPrice,
    });
    const prices = (snap.comps.comps || []).map((c) => c.price).filter((p) => p > 0);
    const median = prices.length
      ? [...prices].sort((a, b) => a - b)[Math.floor(prices.length / 2)]
      : snap.comps.suggestedValue;
    const top = (snap.browse?.items || snap.comps.comps || [])
      .filter((it) => {
        const p = it.price || median;
        return p != null && p >= minPrice && p <= maxPrice;
      })
      .slice(0, 40);
    for (const it of top) {
      const salePrice = it.price || median;
      const soldComps = (snap.comps.comps || []).filter((c) => c.kind === "sold");
      out.push({
        ref: q,
        category,
        id: it.id || it.itemId || null,
        itemId: it.id || it.itemId || null,
        title: it.title || q,
        salePrice,
        suggestedValue: snap.comps.suggestedValue,
        productCost: salePrice ? salePrice * productCostRatio : null,
        productCostEstimated: true,
        leadTimeDays,
        sourcePath,
        retailArbitrage: false,
        activeCount: snap.comps.activeCount ?? snap.browse?.total ?? top.length,
        soldCount: snap.comps.soldCount ?? soldComps.length ?? 0,
        soldEvidenceMissing: snap.comps.soldEvidenceMissing ?? true,
        evidenceStatus: snap.comps.evidenceStatus,
        demandSources: ["ebay_browse", snap.comps.soldCount ? "ebay_insights" : null].filter(Boolean),
        categoryMedianPrice: median,
        url: it.url,
        image: it.image || null,
        images: it.images || (it.image ? [it.image] : []),
        thumbnail: it.thumbnail || it.image || null,
        watchCount: it.watchCount ?? null,
        listingDate: it.listingDate || null,
        seller: it.seller || null,
        soldComps,
        purchaseHistory: soldComps,
        hasImages: Boolean(it.image || (it.images && it.images.length)),
        hasItemSpecifics: true,
        windowDays: 90,
        minSalePrice: minPrice,
        maxSalePrice: maxPrice,
      });
    }
    // Title-only median stubs have no listing URL/image — never treat them as desk products.
    if (!top.length && median && median >= minPrice && median <= maxPrice) {
      out.push({
        ref: q,
        category,
        title: q,
        salePrice: median,
        productCost: median * productCostRatio,
        productCostEstimated: true,
        leadTimeDays,
        sourcePath,
        activeCount: snap.comps.activeCount || 0,
        soldCount: snap.comps.soldCount || 0,
        soldEvidenceMissing: snap.comps.soldEvidenceMissing,
        evidenceStatus: snap.comps.evidenceStatus,
        demandSources: ["ebay_browse"],
        categoryMedianPrice: median,
        minSalePrice: minPrice,
        maxSalePrice: maxPrice,
        synthetic: true,
        url: null,
        image: null,
        images: [],
      });
    }
  }
  return out;
}
