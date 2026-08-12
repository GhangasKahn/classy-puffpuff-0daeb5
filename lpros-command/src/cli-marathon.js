#!/usr/bin/env node
/**
 * Marathon campaign CLI — long multi-category research runs.
 *
 *   npm run marathon -- --q "desk organizer" --variants 250 --details 30
 *   npm run marathon -- --dry --categories 25339,20625,20601
 */
import { pathToFileURL } from "node:url";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { writeFileSync } from "node:fs";
import {
  deployCampaign,
  DEFAULT_MARATHON_CATEGORIES,
} from "./orchestrate/campaign.js";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
await import(pathToFileURL(resolve(root, "ebay-sold-items/src/config.js")).href);

const args = Object.fromEntries(
  process.argv.slice(2).flatMap((a, i, arr) => {
    if (!a.startsWith("--")) return [];
    const k = a.slice(2);
    const v = arr[i + 1] && !arr[i + 1].startsWith("--") ? arr[i + 1] : true;
    return [[k, v]];
  })
);

let categories = DEFAULT_MARATHON_CATEGORIES;
if (args.categories) {
  categories = String(args.categories)
    .split(",")
    .map((id) => id.trim())
    .filter(Boolean)
    .map((id) => {
      const known = DEFAULT_MARATHON_CATEGORIES.find((c) => c.categoryId === id);
      return (
        known || {
          categoryId: id,
          label: id,
          queries: [args.q || "organizer"],
        }
      );
    });
}

console.error(
  `[marathon] ${categories.length} categories · variants/lane=${args.variants || 250} · details/lane=${args.details || 30} · dry=${Boolean(args.dry)}`
);

const job = await deployCampaign(
  {
    mode: "marathon",
    q: args.q || "solid wood desk organizer",
    categories,
    cost: args.cost != null ? Number(args.cost) : 18,
    minPrice: Number(args["min-price"] || 35),
    maxPrice: Number(args["max-price"] || 150),
    suggestedPrice: args.price != null ? Number(args.price) : 59.99,
    variantCount: Number(args.variants || 250),
    detailCount: Number(args.details || 30),
    crawlPages: Number(args["crawl-pages"] || 4),
    crawlLimit: Number(args["crawl-limit"] || 600),
    intelLimit: Number(args.intel || 120),
    liveProbeCount: Number(args.probes || 10),
    ideasTarget: Number(args.ideas || 250),
    dryRun: Boolean(args.dry),
  },
  { sync: true }
);

const out = args.out || `marathon-${job.id}.csv`;
if (job.results?.workbookCsv) {
  writeFileSync(out, job.results.workbookCsv);
  console.error(`[marathon] wrote ${out}`);
}

console.log(
  JSON.stringify(
    {
      jobId: job.id,
      status: job.status,
      error: job.error,
      categoryCount: job.results?.categoryCount,
      productCount: job.results?.productCount,
      productsWithImages: job.results?.productsWithImages,
      variantTotalGenerated: job.results?.variantTotalGenerated,
      ideaCount: job.results?.ideaCount,
      hottest: job.results?.trends?.hottestCategory,
      rising: (job.results?.trends?.risingKeywords || []).slice(0, 8),
      workbook: out,
      lanes: job.results?.lanes,
    },
    null,
    2
  )
);

if (job.status !== "completed") process.exit(1);
