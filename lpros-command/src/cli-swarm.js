#!/usr/bin/env node
import { pathToFileURL } from "node:url";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runResearchSwarm } from "./swarm/research.js";

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

const report = await runResearchSwarm({
  q: args.q || "solid wood desk organizer",
  categoryId: args["category-id"] || "25339",
  categoryLabel: args.category || "Home",
  minPrice: Number(args["min-price"] || 35),
  maxPrice: Number(args["max-price"] || 150),
  costRatio: Number(args["cost-ratio"] || 0.4),
  deepCrawl: Boolean(args.deep),
  crawlPages: Number(args["crawl-pages"] || 2),
  targetDailyProfit: Number(args.target || 50),
});
console.log(JSON.stringify(report, null, 2));
