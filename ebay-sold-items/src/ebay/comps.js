import { searchActiveListings } from "./browse.js";
import { searchSoldItems } from "./insights.js";

/** Rough US category seeds for vault comps. Override with ?categoryIds=. */
export const CATEGORY_SEEDS = {
  watch: "31387",
  watches: "31387",
  wristwatch: "31387",
  "trading card": "183050",
  card: "183050",
  cards: "183050",
  pokemon: "183454",
  whiskey: "2984",
  spirits: "2984",
  wine: "26435",
  car: "6001",
  cars: "6001",
  auto: "6001",
  metal: "39472",
  metals: "39472",
  gold: "39472",
  silver: "39472",
  bullion: "39472",
};

export function resolveCategoryId(category, explicit) {
  if (explicit) return String(explicit);
  if (!category) return undefined;
  const key = String(category).trim().toLowerCase();
  return CATEGORY_SEEDS[key];
}

function median(nums) {
  if (!nums.length) return null;
  const a = [...nums].sort((x, y) => x - y);
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

/** Drop obvious accessory/noise listings that pollute watch/card comps. */
const NOISE_TITLE =
  /\b(hang\s*tag|swing\s*tag|box only|empty box|card only|warranty card only|bezel insert only|for parts|broken|replica|counterfeit)\b/i;

function isNoiseListing(item, ref) {
  if (!item?.title) return true;
  if (NOISE_TITLE.test(item.title)) return true;
  if (item.price == null || !(item.price > 0)) return true;
  // If ref looks like a model number, prefer titles that include it
  if (ref && /^[A-Z0-9-]{5,}$/i.test(ref) && !item.title.toLowerCase().includes(ref.toLowerCase())) {
    // keep but deprioritize later — still allow
  }
  return false;
}

/** If spread is huge, drop prices below 15% of the 75th percentile (accessories). */
function rejectOutlierPrices(prices) {
  if (prices.length < 3) return prices;
  const sorted = [...prices].sort((a, b) => a - b);
  const q75 = sorted[Math.floor(sorted.length * 0.75)] || sorted[sorted.length - 1];
  const floor = q75 * 0.15;
  const filtered = prices.filter((p) => p >= floor);
  return filtered.length ? filtered : prices;
}

function toCompRow(item, sourceLabel) {
  return {
    source: sourceLabel,
    price: item.price,
    date: item.soldDate || item.listingDate || new Date().toISOString().slice(0, 10),
    grade: item.condition || undefined,
    title: item.title,
    url: item.url,
    id: item.id,
    kind: item.kind,
  };
}

/**
 * Build BEDROCK `/v1/market/alt/comps` payload from eBay.
 * Prefers sold (Insights) when entitled; always attaches active Browse comps.
 */
export async function buildAltComps({
  category = "Watch",
  ref = "",
  categoryIds,
  limit = 12,
  includeActive = true,
} = {}) {
  const q = [category, ref].filter(Boolean).join(" ").trim() || ref || category;
  const catId = resolveCategoryId(category, categoryIds);

  let sold = null;
  let soldError = null;
  try {
    sold = await searchSoldItems({
      q: ref || q,
      categoryIds: catId,
      limit,
      sort: "-lastSoldDate",
    });
  } catch (e) {
    soldError = {
      status: e.status || 0,
      message: e.message,
      entitlementLikely: Boolean(e.entitlementLikely),
    };
  }

  let active = null;
  let activeError = null;
  if (includeActive) {
    try {
      active = await searchActiveListings({
        q: ref || q,
        categoryIds: catId,
        limit,
        sort: "price",
      });
    } catch (e) {
      activeError = { status: e.status || 0, message: e.message };
    }
  }

  const soldComps = (sold?.items || [])
    .filter((i) => !isNoiseListing(i, ref))
    .map((i) => toCompRow(i, "eBay sold"));
  const activeComps = (active?.items || [])
    .filter((i) => !isNoiseListing(i, ref))
    .map((i) => toCompRow(i, "eBay active"));

  const preferred = soldComps.length ? soldComps : activeComps;
  const rawPrices = preferred.map((c) => c.price).filter((p) => Number.isFinite(p));
  const prices = rejectOutlierPrices(rawPrices);
  const suggestedValue = median(prices);
  const avgComp =
    prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : null;

  const listingsNeeded = preferred.length === 0;
  const soldEvidenceMissing = soldComps.length === 0;

  const evidenceStatus = soldComps.length
    ? "ok"
    : activeComps.length
      ? "partial"
      : "listings-needed";

  const notes = [];
  if (soldComps.length) {
    notes.push(`eBay Marketplace Insights: ${soldComps.length} sold comps (~90d).`);
  } else if (soldError?.entitlementLikely) {
    notes.push(
      "Marketplace Insights not entitled on this keyset — using active Browse listings. Request Insights access or mark forecasts listings-needed for sold evidence."
    );
  } else if (soldError) {
    notes.push(`Sold search unavailable: ${soldError.message}`);
  }
  if (activeComps.length && !soldComps.length) {
    notes.push(
      `Browse API: ${activeComps.length} active listings (asking prices ≠ sold comps).`
    );
  }
  if (!preferred.length) {
    notes.push("No eBay listings returned — listings-needed.");
  }

  return {
    ref: ref || q,
    category,
    categoryIds: catId || null,
    suggestedValue: suggestedValue != null ? Math.round(suggestedValue) : null,
    avgComp: avgComp != null ? Math.round(avgComp) : null,
    comps: [...soldComps, ...activeComps].slice(0, 24),
    soldCount: soldComps.length,
    activeCount: activeComps.length,
    evidenceStatus,
    listingsNeeded,
    soldEvidenceMissing,
    note: notes.join(" "),
    errors: {
      sold: soldError,
      active: activeError,
    },
    provider: "ebay-sold-items",
  };
}
