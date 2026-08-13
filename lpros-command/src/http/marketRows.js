/**
 * Map any research payload (intel, scout, swarm, orch, playground) onto
 * Market-desk product rows: title, price, image, listing URL, knowledge.
 * Ranker rejection must never hide live Browse listings from the desk.
 */

function uniq(arr) {
  return [...new Set((arr || []).filter(Boolean))];
}

function excerpt(text, n = 400) {
  const s = String(text || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return s.slice(0, n);
}

export function normalizeProduct(item = {}, meta = {}) {
  const images = uniq([
    item.image,
    item.thumbnail,
    ...(Array.isArray(item.images) ? item.images : []),
    ...(Array.isArray(item.additionalImages) ? item.additionalImages : []),
  ]);
  const url = item.url || item.itemWebUrl || "";
  const image = images[0] || "";
  const price = Number(item.price ?? item.salePrice) || 0;
  const specifics = item.itemSpecifics || item.specifics || {};
  return {
    itemId: item.itemId || item.id || item.legacyItemId || "",
    id: item.id || item.itemId || item.legacyItemId || "",
    title: String(item.title || "").trim(),
    price,
    salePrice: Number(item.salePrice ?? item.price) || price,
    url,
    image,
    images,
    imageCount: images.length || Number(item.imageCount) || 0,
    thumbnail: item.thumbnail || image,
    seller: item.seller || "",
    condition: item.condition || "",
    categoryPath: item.categoryPath || item.category || meta.category || "",
    categoryId: item.categoryId || meta.categoryId || "",
    descriptionExcerpt: excerpt(
      item.descriptionExcerpt || item.descriptionText || item.description || item.specificsSummary
    ),
    specificsSummary: item.specificsSummary || excerpt(Object.values(specifics).join(" · "), 160),
    itemSpecifics: specifics,
    perceivedValue: item.perceivedValue ?? null,
    scammy: Boolean(item.scammy),
    rank: item.rank ?? null,
    rankScore: item.rankScore ?? null,
    sellThrough: item.sellThrough ?? null,
    ctrProxy: item.ctrProxy ?? null,
    popularity: item.popularity ?? null,
    net: item.net ?? item.netAtCostRatio ?? null,
    decision: item.decision || "",
    source: item.source || meta.source || "",
    dryRun: Boolean(item.dryRun || item.source === "dry-fixture" || meta.dryRun),
    detailFetched: Boolean(item.detailFetched),
    watchCount: item.watchCount ?? null,
    listingDate: item.listingDate || item.itemCreationDate || null,
  };
}

function bagsFrom(payload = {}) {
  const r = payload.result && typeof payload.result === "object" ? payload.result : {};
  const intel = payload.intel || r.intel || {};
  return [
    payload.products,
    payload.productsPreview,
    payload.items,
    payload.lethalCandidates,
    payload.lethalBoard,
    payload.marketBoard,
    payload.top,
    payload.gallery,
    payload.viz?.gallery,
    payload.scout?.top,
    payload.scout?.market?.board,
    intel.items,
    intel.lethalCandidates,
    r.products,
    r.items,
    r.lethalCandidates,
    r.lethalBoard,
    r.top,
    r.viz?.gallery,
  ];
}

export function collectResearchItems(payload = {}, meta = {}) {
  const out = [];
  const seen = new Set();
  for (const bag of bagsFrom(payload)) {
    if (!Array.isArray(bag)) continue;
    for (const it of bag) {
      const row = normalizeProduct(it, meta);
      if (!row.title) continue;
      const key = row.url || row.itemId || row.title.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(row);
    }
  }
  return out;
}

export function emptyLiveHint({ dryRun = false, configured = true } = {}) {
  if (dryRun) {
    return "Dry-run fixtures only — uncheck Dry-run and run Live product research for real eBay listings, images, and URLs.";
  }
  if (!configured) {
    return "eBay credentials missing. Set EBAY_PRD_APP_ID + EBAY_PRD_CERT_ID and EBAY_ENV=production on this host (Netlify site env, or ebay-sold-items/.env for local :8790).";
  }
  return "Browse returned 0 listings. Check query/category/price band, or run local Command (:8790) — Netlify has no gitignored .env.";
}

export function deskFromResearch(payload = {}, meta = {}) {
  const products = collectResearchItems(payload, meta);
  const dryRun = Boolean(
    payload.dryRun || meta.dryRun || products.some((p) => p.dryRun || p.source === "dry-fixture")
  );
  const withImg = products.filter((p) => p.image).length;
  const withUrl = products.filter((p) => p.url).length;
  let emptyReason = payload.emptyReason || payload.error || meta.emptyReason || null;
  if (!products.length) {
    emptyReason = emptyReason || emptyLiveHint({ dryRun, configured: meta.configured !== false });
  } else if (dryRun) {
    emptyReason =
      emptyReason ||
      "Dry-run — these are synthetic titles, not live eBay products. Run Live product research.";
  }
  return {
    products,
    productsPreview: products.slice(0, 80),
    productCount: products.length,
    productsWithImages: withImg,
    productsWithUrls: withUrl,
    dryRun,
    emptyReason,
    query: meta.query || payload.query || payload.q || payload.mission?.q || null,
  };
}

export function deskFromPlaygroundJobs(jobs = [], meta = {}) {
  const payloads = (jobs || []).map((j) => j?.result || j || {});
  const merged = {
    dryRun: (jobs || []).some((j) => j?.result?.dryRun || j?.input?.dryRun || j?.dryRun),
    products: payloads.flatMap((p) => collectResearchItems(p, meta)),
  };
  return deskFromResearch(merged, {
    ...meta,
    dryRun: merged.dryRun,
    query: meta.query || jobs[0]?.input?.q,
  });
}

export function noLiveProductsError(message) {
  const err = new Error(message || emptyLiveHint());
  err.status = 422;
  err.code = "NO_LIVE_PRODUCTS";
  return err;
}
