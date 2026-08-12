/**
 * Mine useful signals from official Browse item detail (not HTML scrape).
 */
import { stripHtml } from "../../../ebay-sold-items/src/ebay/browse.js";
import { scoreImageSeo } from "./seo.js";
import { psychProxies } from "./psychology.js";

/**
 * Normalize a researched product row for boards + CSV.
 */
export function toProductResearchRow(item, meta = {}) {
  const images = item.images?.length ? item.images : item.image ? [item.image] : [];
  const imageSeo = scoreImageSeo(images, { hasLifestyle: images.length >= 3 });
  const psych = psychProxies({
    title: item.title || "",
    salePrice: item.price ?? item.salePrice,
    categoryMedianPrice: meta.medianPrice ?? item.categoryMedianPrice ?? item.price,
  });
  const specifics = item.itemSpecifics || {};
  const desc = item.descriptionText || stripHtml(item.descriptionHtml || "");

  return {
    kind: "PRODUCT_RESEARCH",
    itemId: item.id || item.rawItemId,
    title: item.title,
    price: item.price ?? item.salePrice,
    currency: item.currency || "USD",
    url: item.url,
    image: images[0] || null,
    images,
    imageCount: images.length,
    imageSeoScore: Math.round((imageSeo.imageScore || 0) * 100),
    imageRecommendations: imageSeo.recommendations,
    seller: item.seller,
    sellerFeedback: item.sellerFeedback,
    condition: item.condition,
    brand: item.brand || specifics.Brand || null,
    categoryPath: item.categoryPath || meta.categoryPath || null,
    categoryId: item.categoryIdLeaf || meta.categoryId || null,
    itemSpecifics: specifics,
    specificsSummary: Object.entries(specifics)
      .slice(0, 12)
      .map(([k, v]) => `${k}: ${v}`)
      .join(" | "),
    descriptionExcerpt: desc.slice(0, 500),
    descriptionLength: desc.length,
    watchCount: item.watchCount,
    quantityAvailable: item.quantityAvailable,
    shippingOptions: item.shippingOptions || [],
    returnTerms: item.returnTerms || null,
    perceivedValue: item.perceivedValue ?? psych.perceivedValue,
    scammy: item.scammy ?? psych.scammy,
    psychFit: item.psychFit ?? psych.psychFit,
    rank: item.rank,
    rankScore: item.rankScore,
    sellThrough: item.sellThrough,
    ctrProxy: item.ctrProxy,
    popularity: item.popularity,
    detailFetched: item.detailFetched === true,
    contentSignals: extractContentSignals(desc, item.title, specifics),
    researchedAt: new Date().toISOString(),
    jobId: meta.jobId || null,
    sourceQuery: meta.query || null,
  };
}

export function extractContentSignals(descriptionText, title, specifics = {}) {
  const blob = `${title || ""} ${descriptionText || ""} ${Object.values(specifics).join(" ")}`.toLowerCase();
  const signals = [];
  if (/solid wood|oak|walnut|bamboo|hardwood/.test(blob)) signals.push("material_premium");
  if (/organiz|clutter|cable|storage|drawer/.test(blob)) signals.push("problem_solve");
  if (/upgrade|premium|professional|heavy duty/.test(blob)) signals.push("upgrade_language");
  if (/dimension|inch|"|cm|measure/.test(blob)) signals.push("size_trust");
  if (/gift|office|home office|desk/.test(blob)) signals.push("use_case_clear");
  if (/free shipping|fast ship/.test(blob)) signals.push("shipping_hook");
  if (/warranty|return|guarantee/.test(blob)) signals.push("risk_reversal");
  if (/\b\d+\s*(pcs|piece|pack|lot)\b/.test(blob)) signals.push("qty_spam_risk");
  return signals;
}

/**
 * Product research CSV (real listings — images, URLs, content).
 */
export function productsToCsv(rows) {
  const cols = [
    "rank",
    "itemId",
    "title",
    "price",
    "url",
    "image",
    "imageCount",
    "imageSeoScore",
    "seller",
    "condition",
    "brand",
    "categoryPath",
    "specificsSummary",
    "descriptionExcerpt",
    "contentSignals",
    "perceivedValue",
    "scammy",
    "rankScore",
    "sellThrough",
    "ctrProxy",
    "popularity",
    "detailFetched",
    "sourceQuery",
    "jobId",
    "researchedAt",
  ];
  const esc = (v) => {
    if (v == null) return "";
    const s = Array.isArray(v) ? v.join(" | ") : String(v);
    if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  const header = cols.join(",");
  const lines = rows.map((r, i) =>
    cols
      .map((c) => {
        if (c === "rank") return esc(r.rank ?? i + 1);
        return esc(r[c]);
      })
      .join(",")
  );
  return [header, ...lines].join("\n") + "\n";
}
