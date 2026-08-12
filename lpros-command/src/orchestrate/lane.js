/**
 * Single-category research lane — used by single missions and marathon campaigns.
 */
import { crawlCategory } from "../../../lpros/src/agents/crawl.js";
import { competitorIntel } from "../intel/competitor.js";
import {
  mineKeywordPatterns,
  generateTitleVariations,
  scoreTitleSeo,
  imageSeoChecklist,
  buildConversionDescription,
  extractKeywordsFromTitle,
} from "../../../lpros/src/core/seo.js";
import { toDecisionCsv } from "../../../lpros/src/core/spreadsheet.js";
import {
  toProductResearchRow,
  extractContentSignals,
} from "../../../lpros/src/core/listing_content.js";
import { netProfitPerSale } from "../../../lpros/src/core/economics.js";
import {
  searchActiveListings,
  enrichItemsWithDetails,
} from "../../../ebay-sold-items/src/ebay/browse.js";
import {
  keywordMomentum,
  categoryTrendSnapshot,
} from "../../../lpros/src/core/trends.js";

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function median(nums) {
  const a = nums.filter((n) => Number.isFinite(n)).sort((x, y) => x - y);
  if (!a.length) return null;
  return a[Math.floor(a.length / 2)];
}

async function probeTitleLive(title, categoryId, limit = 20) {
  try {
    const res = await searchActiveListings({
      q: title.slice(0, 80),
      categoryIds: categoryId || undefined,
      limit,
      sort: "bestMatch",
    });
    const items = res.items || [];
    const prices = items.map((it) => Number(it.price)).filter((n) => Number.isFinite(n));
    const withImg = items.filter((it) => it.image || (it.images || []).length).length;
    return {
      liveTotal: res.total ?? items.length,
      liveMedianPrice: median(prices),
      liveImageCoverage: items.length ? withImg / items.length : null,
      competitionProxy: Math.min(100, Math.round(((res.total || items.length) / 100) * 2)),
    };
  } catch (e) {
    return { liveError: e.message, liveTotal: null, competitionProxy: null };
  }
}

function scoreVariants(rawVariants, patterns, { cost, priceHint, categoryId, categoryLabel }) {
  return rawVariants
    .filter((v) => !v.scammy)
    .map((v) => {
      const seo = scoreTitleSeo(v.title, patterns, { salePrice: priceHint });
      const kw = extractKeywordsFromTitle(v.title, patterns);
      const econ = netProfitPerSale({ salePrice: priceHint, productCost: cost });
      const imageSeo = imageSeoChecklist({ title: v.title, primaryKeyword: kw.primaryKeyword });
      const description = buildConversionDescription({
        title: v.title,
        keywords: kw.secondaryKeywords,
        material: (patterns.materialDemand || [])[0]?.term,
        price: priceHint,
      });
      const seoPct = Math.round((seo.seoScore || 0) * 100);
      return {
        ...v,
        seoScore: seoPct,
        primaryKeyword: kw.primaryKeyword,
        secondaryKeywords: kw.secondaryKeywords,
        outrankAdvice: seo.outrankAdvice,
        suggestedPrice: priceHint,
        landedCost: cost,
        estFees: econ.fees,
        estNet: econ.net,
        estMarginPct: econ.marginPct,
        imageSeo,
        description,
        competitionProxy: null,
        liveTotal: null,
        liveMedianPrice: null,
        liveImageCoverage: null,
        variantFamily: v.family || "base",
        testPriority: seoPct >= 70 ? "A" : seoPct >= 55 ? "B" : "C",
        categoryId,
        categoryPath: categoryLabel,
      };
    })
    .sort((a, b) => (b.seoScore || 0) - (a.seoScore || 0));
}

/**
 * Research one category lane end-to-end.
 * @param {object} lane
 * @param {object} opts
 * @param {(level:string,msg:string,data?:object)=>void} [opts.log]
 */
export async function researchCategoryLane(lane, opts = {}) {
  const log = opts.log || (() => {});
  const cost = Number(opts.cost) || 18;
  const minPrice = opts.minPrice ?? 35;
  const maxPrice = opts.maxPrice ?? 200;
  const categoryId = lane.categoryId || lane.id;
  const label = lane.label || lane.category || categoryId || "Category";
  const queries = [
    lane.query,
    ...(lane.queries || lane.seedQueries || []),
    ...(opts.globalQueries || []),
  ]
    .filter(Boolean)
    .map(String);
  const primaryQ = queries[0] || opts.defaultQuery || "organizer";

  log("info", `[${label}] Intel + multi-query Browse (${queries.length} queries)`, {
    phase: "intel",
    categoryId,
  });

  // Multi-query intel — merge lethal boards
  const midPrice = (minPrice + maxPrice) / 2;
  const costRatio = Math.min(0.85, cost / Math.max(midPrice, 1));
  const intelLimit = opts.intelLimit || 100;
  let mergedIntel = null;
  const lethalMap = new Map();
  const allTitles = [];

  for (const q of queries.slice(0, opts.maxQueriesPerCategory || 6)) {
    try {
      const intel = await competitorIntel({
        q,
        categoryId,
        minPrice,
        maxPrice,
        limit: intelLimit,
        productCostRatio: costRatio,
      });
      if (!mergedIntel) mergedIntel = intel;
      else {
        mergedIntel.market.activeTotal = Math.max(
          mergedIntel.market?.activeTotal || 0,
          intel.market?.activeTotal || 0
        );
        mergedIntel.market.sampleSize =
          (mergedIntel.market?.sampleSize || 0) + (intel.market?.sampleSize || 0);
      }
      for (const c of intel.lethalCandidates || []) {
        if (c.id && !lethalMap.has(c.id)) lethalMap.set(c.id, c);
        if (c.title) allTitles.push(c.title);
      }
      log("debug", `[${label}] query "${q}" → ${intel.lethalCandidates?.length || 0} board rows`, {
        phase: "intel",
      });
    } catch (e) {
      log("warn", `[${label}] intel soft-fail for "${q}": ${e.message}`, { phase: "intel" });
    }
    await sleep(opts.queryDelayMs || 250);
  }

  const lethalCandidates = [...lethalMap.values()].slice(0, opts.boardCap || 120);
  if (!lethalCandidates.length && !mergedIntel?.market?.sampleSize) {
    throw new Error(`Zero products in lane ${label} (${categoryId})`);
  }

  // Fresh vs baseline for momentum
  let freshTitles = [];
  let baselineTitles = [...allTitles];
  let newlyListedMedian = null;
  let bestMatchMedian = null;
  try {
    const [fresh, base] = await Promise.all([
      searchActiveListings({
        q: primaryQ,
        categoryIds: categoryId,
        minPrice,
        maxPrice,
        limit: Math.min(intelLimit, 100),
        sort: "newlyListed",
      }),
      searchActiveListings({
        q: primaryQ,
        categoryIds: categoryId,
        minPrice,
        maxPrice,
        limit: Math.min(intelLimit, 100),
        sort: "bestMatch",
      }),
    ]);
    freshTitles = (fresh.items || []).map((i) => i.title).filter(Boolean);
    baselineTitles = (base.items || []).map((i) => i.title).filter(Boolean);
    newlyListedMedian = median((fresh.items || []).map((i) => i.price));
    bestMatchMedian = median((base.items || []).map((i) => i.price));
    for (const it of fresh.items || []) {
      if (it.id && !lethalMap.has(it.id)) {
        lethalMap.set(it.id, {
          ...it,
          salePrice: it.price,
          perceivedValue: 0.5,
        });
      }
    }
  } catch (e) {
    log("warn", `[${label}] momentum sample soft-fail: ${e.message}`, { phase: "trends" });
  }

  // Crawl
  let crawl = null;
  try {
    log("info", `[${label}] Crawl Browse pagination`, { phase: "crawl" });
    crawl = await crawlCategory({
      categoryId,
      q: primaryQ,
      minPrice,
      maxPrice,
      maxPages: opts.crawlPages || 2,
      maxItems: opts.crawlLimit || 200,
      delayMs: opts.crawlDelayMs || 300,
      applyQualityFilter: true,
      outPrefix: `lane-${categoryId}-${Date.now().toString(36)}`,
    });
    log(
      "info",
      `[${label}] Crawl kept ${crawl?.kept ?? 0} / raw ${crawl?.rawCount ?? 0}`,
      { phase: "crawl" }
    );
  } catch (e) {
    log("warn", `[${label}] crawl soft-fail: ${e.message}`, { phase: "crawl" });
  }

  const boardSeed = [...lethalMap.values()].slice(0, opts.detailCount || 12);
  log("info", `[${label}] getItem detail for ${boardSeed.length} products`, { phase: "detail" });
  const detailed = await enrichItemsWithDetails(boardSeed, {
    max: opts.detailCount || 12,
    delayMs: opts.detailDelayMs || 220,
  });

  const medianPrice = mergedIntel?.market?.priceLadder?.p50 || bestMatchMedian;
  const products = detailed.map((it, i) =>
    toProductResearchRow(
      { ...it, rank: it.rank || i + 1 },
      {
        jobId: opts.jobId,
        query: primaryQ,
        categoryId,
        categoryPath: label,
        medianPrice,
      }
    )
  );

  for (const t of crawl?.topByPerceivedValue || []) {
    if (products.some((p) => p.title === t.title)) continue;
    if (products.length >= (opts.detailCount || 12) + 10) break;
    products.push(
      toProductResearchRow(
        {
          id: null,
          title: t.title,
          price: t.price,
          url: t.url,
          image: null,
          images: [],
          perceivedValue: t.perceivedValue,
          scammy: t.scammy,
          descriptionText: "",
          itemSpecifics: {},
          detailFetched: false,
          rank: products.length + 1,
        },
        { jobId: opts.jobId, query: primaryQ, categoryId, categoryPath: label }
      )
    );
  }

  const competitorTitles = [
    ...products.map((p) => p.title),
    ...products.map((p) => p.descriptionExcerpt),
    ...allTitles,
    ...freshTitles,
  ].filter(Boolean);
  const patterns = mineKeywordPatterns(competitorTitles);
  const momentum = keywordMomentum({
    freshTitles,
    baselineTitles: baselineTitles.length ? baselineTitles : allTitles,
  });

  const variantCount = opts.variantCount || 200;
  log("info", `[${label}] Title swarm ${variantCount} variants`, { phase: "swarm" });
  const rawVariants = generateTitleVariations({
    seed: primaryQ,
    categoryHint: label,
    maxTitles: variantCount,
    patterns,
  });
  const priceHint = Number(opts.suggestedPrice) || medianPrice || products[0]?.price || 59.99;
  let scored = scoreVariants(rawVariants, patterns, {
    cost,
    priceHint,
    categoryId,
    categoryLabel: label,
  });

  const probeN = Math.min(opts.liveProbeCount ?? 8, 25);
  for (let i = 0; i < probeN; i++) {
    const row = scored[i];
    if (!row) break;
    Object.assign(row, await probeTitleLive(row.title, categoryId, 20));
    if (row.competitionProxy > 70 && row.testPriority === "A") row.testPriority = "B";
    await sleep(opts.probeDelayMs || 300);
  }

  const sheetRows = Math.min(opts.sheetRows || 150, scored.length);
  const topForSheet = scored.slice(0, sheetRows);
  const refImage = products.find((p) => p.image)?.image;
  const refUrl = products.find((p) => p.url)?.url;
  for (const row of topForSheet) {
    row.refCompetitorImage = refImage;
    row.refCompetitorUrl = refUrl;
    row.contentSignals = extractContentSignals(row.title, row.title, {});
    row.sourceQuery = primaryQ;
  }
  const sheet = toDecisionCsv(topForSheet, {
    jobId: opts.jobId,
    query: primaryQ,
    categoryId,
    categoryPath: label,
    landedCost: cost,
    suggestedPrice: priceHint,
    loggedAt: new Date().toISOString(),
  });

  const avgImageCount =
    products.length > 0
      ? products.reduce((s, p) => s + (p.imageCount || 0), 0) / products.length
      : 0;

  const snapshot = categoryTrendSnapshot({
    categoryId,
    label,
    query: primaryQ,
    activeTotal: mergedIntel?.market?.activeTotal,
    sampleSize: lethalCandidates.length || mergedIntel?.market?.sampleSize,
    priceLadder: mergedIntel?.market?.priceLadder,
    newlyListedMedian,
    bestMatchMedian,
    sellerHhi: mergedIntel?.market?.sellerConcentrationHHI,
    density: mergedIntel?.market?.density,
    productCount: products.length,
    avgImageCount,
    topKeywords: (patterns.topUnigrams || []).slice(0, 12),
  });

  log(
    "info",
    `[${label}] Lane done — ${products.length} products · ${sheet.rows.length} variants · heat ${snapshot.heatScore}`,
    { phase: "lane_done" }
  );

  return {
    categoryId,
    label,
    queries,
    primaryQ,
    intel: mergedIntel,
    products,
    patterns,
    momentum,
    snapshot,
    titles: competitorTitles.slice(0, 500),
    variants: sheet.rows,
    variantTotalGenerated: scored.length,
    spreadsheetCsv: sheet.csv,
    scored,
  };
}

/** Dry lane for tests */
export function researchCategoryLaneDry(lane, opts = {}) {
  const categoryId = lane.categoryId || lane.id || "25339";
  const label = lane.label || "Dry";
  const primaryQ = lane.query || lane.queries?.[0] || opts.defaultQuery || "desk organizer";
  const titles = [
    `Solid wood ${primaryQ} oak`,
    `Bamboo ${primaryQ} clutter solution`,
    `Walnut ${primaryQ} premium upgrade`,
    `Minimalist steel ${primaryQ} cable management`,
  ];
  const patterns = mineKeywordPatterns(titles);
  const fresh = titles.slice(0, 2).map((t) => `new ${t}`);
  const momentum = keywordMomentum({ freshTitles: fresh, baselineTitles: titles });
  const products = titles.map((title, i) =>
    toProductResearchRow(
      {
        id: `dry_${categoryId}_${i}`,
        title,
        price: 45 + i * 4,
        url: `https://www.ebay.com/itm/dry${categoryId}${i}`,
        image: i % 2 === 0 ? `https://i.ebayimg.com/images/g/dry/s-l1600.jpg` : null,
        images: i % 2 === 0 ? [`https://i.ebayimg.com/images/g/dry/s-l1600.jpg`] : [],
        descriptionText: `${title}. Dimensions 12 inch. Home office storage.`,
        itemSpecifics: { Material: "Wood" },
        detailFetched: true,
        rank: i + 1,
      },
      { jobId: opts.jobId, query: primaryQ, categoryId, categoryPath: label }
    )
  );
  const raw = generateTitleVariations({
    seed: primaryQ,
    maxTitles: opts.variantCount || 40,
    patterns,
  });
  const scored = scoreVariants(raw, patterns, {
    cost: opts.cost || 18,
    priceHint: opts.suggestedPrice || 59.99,
    categoryId,
    categoryLabel: label,
  });
  const sheet = toDecisionCsv(scored.slice(0, 30), {
    jobId: opts.jobId,
    query: primaryQ,
    categoryId,
    categoryPath: label,
  });
  const snapshot = categoryTrendSnapshot({
    categoryId,
    label,
    query: primaryQ,
    activeTotal: 800 + Number(categoryId) % 500,
    sampleSize: products.length,
    priceLadder: { p10: 35, p50: 49, p75: 62, p90: 80 },
    newlyListedMedian: 52,
    bestMatchMedian: 49,
    density: 12,
    productCount: products.length,
    avgImageCount: 1,
    topKeywords: patterns.topUnigrams?.slice(0, 8),
  });
  return {
    categoryId,
    label,
    queries: [primaryQ],
    primaryQ,
    intel: { market: { activeTotal: snapshot.activeTotal, sampleSize: 4, priceLadder: snapshot.priceLadder } },
    products,
    patterns,
    momentum,
    snapshot,
    titles,
    variants: sheet.rows,
    variantTotalGenerated: scored.length,
    spreadsheetCsv: sheet.csv,
    scored,
  };
}
