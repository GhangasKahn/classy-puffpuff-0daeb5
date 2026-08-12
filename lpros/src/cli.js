#!/usr/bin/env node
/**
 * LPROS CLI
 *   node src/cli.js econ --price 40 --cost 22
 *   node src/cli.js forecast --listings 300 --str 0.018 --net 9.4 --target 120
 *   node src/cli.js verify --price 40 --cost 22
 *   node src/cli.js pipeline --category Watch --q 126610LN --cost-ratio 0.55
 */
import { loadEbayEnv } from "./agents/_env.js";
import {
  netProfitPerSale,
  listingsNeeded,
  expectedDailyProfit,
  stressForecast,
} from "./core/economics.js";
import { verifyProduct } from "./core/verify.js";
import { runResearchPipeline } from "./pipeline.js";
import { crawlCategory, crawlSubtree } from "./agents/crawl.js";

const [cmd, ...rest] = process.argv.slice(2);
const args = parseArgs(rest);

async function main() {
  if (!cmd || cmd === "help" || cmd === "-h") {
    console.log(`LPROS — Lean Product Research OS

Commands:
  econ          Net profit after eBay fees
  forecast      Daily profit + listings-needed (Base/Adverse/Severe)
  verify        Zero-trust multi-factor gate on a product
  pipeline      Live eBay research → rank (needs ebay-sold-items/.env)
  rank          Alias for pipeline
  crawl         Paginate ALL active listings in a category (Browse API)
  crawl-subtree Discover leaf categories under a parent, crawl each

Crawl examples:
  npm run crawl -- --category-id 43510 --min-price 35 --max-pages 10
  npm run crawl -- --category-id 63514 --q organizer --max-items 500
  npm run crawl-subtree -- --root 63514 --max-leaves 5 --max-pages 3

Note: Uses official eBay Browse/Taxonomy APIs only — not HTML scraping.
`);
    return;
  }

  if (cmd === "econ") {
    const r = netProfitPerSale({
      salePrice: num(args.price, 40),
      shippingCharged: num(args.shipping, 0),
      productCost: num(args.cost, 22),
      returnsBufferRate: num(args.returns, 0.04),
      hasStore: Boolean(args.store),
      toolAmortPerSale: num(args.tool, 0),
    });
    console.log(JSON.stringify(r, null, 2));
    return;
  }

  if (cmd === "forecast") {
    const listings = num(args.listings, 300);
    const str = num(args.str, 0.018);
    const avgNet = num(args.net, 9.4);
    const target = num(args.target, 120);
    const out = {
      expected: expectedDailyProfit({ listings, str, avgNet }),
      needed: listingsNeeded({ targetDailyProfit: target, str, avgNet }),
      stress: stressForecast({ listings, str, avgNet, targetDailyProfit: target }),
    };
    console.log(JSON.stringify(out, null, 2));
    return;
  }

  if (cmd === "verify") {
    const price = num(args.price, 40);
    const cost = num(args.cost, 22);
    const r = verifyProduct({
      salePrice: price,
      productCost: cost,
      altProductCost: args.altCost != null ? num(args.altCost) : null,
      leadTimeDays: num(args.lead, 7),
      activeCount: num(args.active, 40),
      soldCount: num(args.sold, 5),
      soldEvidenceMissing: num(args.sold, 5) === 0,
      evidenceStatus: num(args.sold, 5) > 0 ? "ok" : "partial",
      demandConfidence: num(args.dconf, 0.4),
      density: num(args.density, 200),
      velocityPerDay: num(args.vel, 0.5),
      remorseRisk: num(args.remorse, 0.3),
      retailArbitrage: Boolean(args.arbitrage),
      sourcePath: args.source || "wholesale",
      title: args.title || "sample product",
      demandSources: ["ebay_browse", "terapeak"],
    });
    console.log(JSON.stringify(r, null, 2));
    return;
  }

  if (cmd === "pipeline" || cmd === "rank") {
    await loadEbayEnv();
    const queries = String(args.q || args.query || "126610LN")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const report = await runResearchPipeline({
      category: args.category || "Watch",
      queries,
      productCostRatio: num(args["cost-ratio"], 0.45),
      leadTimeDays: num(args.lead, 7),
      sourcePath: args.source || "wholesale_unspecified",
      targetDailyProfit: num(args.target, 50),
      assumedStr: num(args.str, 0.015),
      minPrice: num(args["min-price"], 35),
      maxPrice: num(args["max-price"], 200),
      thresholds: {
        minMargin: num(args["min-margin"], 0.12),
        minSalePrice: num(args["min-price"], 35),
        maxSalePrice: num(args["max-price"], 200),
      },
    });
    console.log(JSON.stringify(report, null, 2));
    return;
  }

  if (cmd === "crawl") {
    const summary = await crawlCategory({
      categoryId: args["category-id"] || args.categoryId || args.cat,
      q: args.q || args.query,
      minPrice: num(args["min-price"], 35),
      maxPrice: num(args["max-price"], 200),
      maxPages: num(args["max-pages"], 25),
      maxItems: num(args["max-items"], 2000),
      pageSize: num(args["page-size"], 200),
      delayMs: num(args.delay, 400),
      sort: args.sort || "newlyListed",
      applyQualityFilter: !args["no-filter"],
      minPerceivedValue: num(args["min-pv"], 0.25),
      outPrefix: args.out,
    });
    console.log(JSON.stringify(summary, null, 2));
    return;
  }

  if (cmd === "crawl-subtree") {
    const rollup = await crawlSubtree({
      rootCategoryId: String(args.root || args["root-id"] || args["category-id"] || ""),
      maxLeaves: num(args["max-leaves"], 10),
      maxPagesPerLeaf: num(args["max-pages"], 5),
      maxItemsPerLeaf: num(args["max-items"], 400),
      minPrice: num(args["min-price"], 35),
      maxPrice: num(args["max-price"], 200),
      delayMs: num(args.delay, 400),
      applyQualityFilter: !args["no-filter"],
    });
    console.log(JSON.stringify(rollup, null, 2));
    return;
  }

  console.error(`Unknown command: ${cmd}`);
  process.exit(1);
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (!next || next.startsWith("--")) out[key] = true;
      else {
        out[key] = next;
        i++;
      }
    }
  }
  return out;
}

function num(v, d) {
  if (v == null || v === true) return d;
  const n = Number(v);
  return Number.isFinite(n) ? n : d;
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
