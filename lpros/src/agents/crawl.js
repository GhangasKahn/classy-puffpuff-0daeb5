/**
 * Category crawler — official eBay Browse + Taxonomy APIs only.
 * Does NOT scrape ebay.com HTML (ToS / account risk).
 *
 * Paginates active listings in one or more category IDs, applies price band +
 * scam/value filters, writes JSONL + summary JSON under data/crawls/.
 */
import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { loadEbayEnv } from "./_env.js";
import { iterateCategoryListings } from "../../../ebay-sold-items/src/ebay/browse.js";
import { getCategorySubtree, collectLeaves, getDefaultCategoryTreeId } from "../ebay/taxonomy.js";
import { psychProxies } from "../core/psychology.js";

const dataDir = resolve(dirname(fileURLToPath(import.meta.url)), "../../data/crawls");

/**
 * Crawl a single category (or keyword+category) with pagination.
 */
export async function crawlCategory({
  categoryId,
  q,
  minPrice = 35,
  maxPrice = 200,
  maxPages = 25,
  maxItems = 2000,
  pageSize = 200,
  delayMs = 400,
  sort = "newlyListed",
  applyQualityFilter = true,
  minPerceivedValue = 0.25,
  outPrefix,
} = {}) {
  await loadEbayEnv();
  if (!categoryId && !q) throw new Error("Provide --category-id and/or --q");

  if (!existsSync(dataDir)) mkdirSync(dataDir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const tag = outPrefix || `cat-${categoryId || "q"}-${stamp}`;
  const jsonlPath = resolve(dataDir, `${tag}.jsonl`);
  const summaryPath = resolve(dataDir, `${tag}.summary.json`);

  const kept = [];
  const rejected = [];
  let pages = 0;
  let apiTotal = null;
  let rawCount = 0;

  writeFileSync(jsonlPath, ""); // truncate

  for await (const batch of iterateCategoryListings({
    categoryIds: categoryId,
    q,
    minPrice,
    maxPrice,
    sort,
    pageSize,
    maxPages,
    maxItems,
    delayMs,
  })) {
    pages = batch.page;
    apiTotal = batch.total;
    for (const item of batch.items) {
      rawCount += 1;
      const psych = psychProxies({
        title: item.title || "",
        salePrice: item.price,
        categoryMedianPrice: item.price,
      });
      const row = {
        crawledAt: new Date().toISOString(),
        categoryId: categoryId || null,
        query: q || null,
        ...item,
        psychFit: psych.psychFit,
        perceivedValue: psych.perceivedValue,
        variationPotential: psych.variationPotential,
        remorseRisk: psych.remorseRisk,
        scammy: psych.scammy,
        scamHits: psych.scamHits,
        killRecommendation: psych.killRecommendation,
        psychNotes: psych.notes,
      };

      const inBand =
        item.price != null && item.price >= minPrice && item.price <= maxPrice;
      const qualityOk =
        !applyQualityFilter ||
        (!psych.scammy &&
          !psych.killRecommendation &&
          (psych.perceivedValue >= minPerceivedValue ||
            psych.features.problemSolving ||
            psych.features.upgradeReplace));

      if (inBand && qualityOk) {
        kept.push(row);
        writeFileSync(jsonlPath, JSON.stringify(row) + "\n", { flag: "a" });
      } else {
        rejected.push({
          id: item.id,
          title: item.title,
          price: item.price,
          scammy: psych.scammy,
          scamHits: psych.scamHits,
          perceivedValue: psych.perceivedValue,
          reason: !inBand ? "price_band" : psych.scammy ? "scammy" : "low_value",
        });
      }
    }
    console.error(
      `[crawl] page ${batch.page} +${batch.items.length} (fetched ${batch.fetched}/${batch.total ?? "?"}) kept=${kept.length} rejected=${rejected.length}`
    );
  }

  const summary = {
    generatedAt: new Date().toISOString(),
    method: "ebay_browse_api",
    note: "Official Browse API pagination — not HTML scraping.",
    categoryId: categoryId || null,
    query: q || null,
    priceBand: { min: minPrice, max: maxPrice },
    pages,
    apiTotal,
    rawCount,
    kept: kept.length,
    rejected: rejected.length,
    applyQualityFilter,
    minPerceivedValue,
    jsonlPath,
    topByPerceivedValue: [...kept]
      .sort((a, b) => (b.perceivedValue || 0) - (a.perceivedValue || 0))
      .slice(0, 15)
      .map(brief),
    rejectSample: rejected.slice(0, 10),
  };
  writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
  return summary;
}

/**
 * Discover leaf categories under a parent, optionally crawl each (capped).
 */
export async function crawlSubtree({
  rootCategoryId,
  maxLeaves = 10,
  maxPagesPerLeaf = 5,
  maxItemsPerLeaf = 400,
  minPrice = 35,
  maxPrice = 200,
  delayMs = 400,
  applyQualityFilter = true,
} = {}) {
  await loadEbayEnv();
  await getDefaultCategoryTreeId();
  const tree = await getCategorySubtree(rootCategoryId);
  const root = tree.categorySubtreeNode || tree.category_subtree_node || tree;
  const leaves = collectLeaves(root).slice(0, maxLeaves);

  const results = [];
  for (const leaf of leaves) {
    console.error(`[crawl-subtree] leaf ${leaf.id} ${leaf.name}`);
    const summary = await crawlCategory({
      categoryId: leaf.id,
      minPrice,
      maxPrice,
      maxPages: maxPagesPerLeaf,
      maxItems: maxItemsPerLeaf,
      delayMs,
      applyQualityFilter,
      outPrefix: `leaf-${leaf.id}`,
    });
    results.push({
      leafId: leaf.id,
      leafName: leaf.name,
      kept: summary.kept,
      rawCount: summary.rawCount,
      apiTotal: summary.apiTotal,
      jsonlPath: summary.jsonlPath,
    });
  }

  const rollup = {
    generatedAt: new Date().toISOString(),
    rootCategoryId,
    leavesCrawled: results.length,
    results,
  };
  if (!existsSync(dataDir)) mkdirSync(dataDir, { recursive: true });
  const rollupPath = resolve(
    dataDir,
    `subtree-${rootCategoryId}-${new Date().toISOString().replace(/[:.]/g, "-")}.json`
  );
  writeFileSync(rollupPath, JSON.stringify(rollup, null, 2));
  return { ...rollup, rollupPath };
}

function brief(r) {
  return {
    title: (r.title || "").slice(0, 90),
    price: r.price,
    perceivedValue: r.perceivedValue,
    psychFit: r.psychFit,
    url: r.url,
    scammy: r.scammy,
  };
}
