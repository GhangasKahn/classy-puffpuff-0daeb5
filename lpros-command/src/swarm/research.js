/**
 * Hermes-style research swarm — parallel specialist agents, Brain merge.
 * Low-compute: sequential/light-parallel JS agents (no GPU required).
 * Optional: wire local Ollama/Hermes later for copy generation.
 */
import { competitorIntel } from "../intel/competitor.js";
import { crawlCategory } from "../../../lpros/src/agents/crawl.js";
import { runResearchPipeline } from "../../../lpros/src/pipeline.js";
import {
  expectedDailyProfit,
  listingsNeeded,
  stressForecast,
  netProfitPerSale,
} from "../../../lpros/src/core/economics.js";

/**
 * Run the research swarm for a query / category.
 * Agents: Scout → Intel → Quality → Economics → Brain (merge)
 */
export async function runResearchSwarm({
  q,
  categoryId,
  categoryLabel = "Home",
  minPrice = 35,
  maxPrice = 200,
  costRatio = 0.4,
  crawlPages = 2,
  targetDailyProfit = 50,
  assumedStr = 0.015,
  deepCrawl = false,
} = {}) {
  const started = Date.now();
  const log = [];
  const note = (agent, msg) => log.push({ ts: new Date().toISOString(), agent, msg });

  note("Brain", "Mission: find lethal, high-perceived-value SKUs — kill scammy dropship junk");

  // 1. Scout — fast pipeline rank
  note("Scout", `Pipeline probe for "${q}"`);
  const scout = await runResearchPipeline({
    category: categoryLabel,
    queries: [q],
    productCostRatio: costRatio,
    minPrice,
    maxPrice,
    targetDailyProfit,
    assumedStr,
  });

  // 2. Intel — competitor landscape (ZIK-class)
  note("Intel", "Competitor density, price ladder, seller HHI");
  const intel = await competitorIntel({
    q,
    categoryId,
    minPrice,
    maxPrice,
    limit: 100,
    productCostRatio: costRatio,
  });

  // 3. Deep crawl (optional) — category saturation sample
  let crawl = null;
  if (deepCrawl && categoryId) {
    note("Crawler", `Deep Browse crawl category ${categoryId} (${crawlPages} pages)`);
    crawl = await crawlCategory({
      categoryId,
      q,
      minPrice,
      maxPrice,
      maxPages: crawlPages,
      maxItems: crawlPages * 200,
      delayMs: 300,
      applyQualityFilter: true,
      outPrefix: `swarm-${categoryId}`,
    });
  } else {
    note("Crawler", "Skipped (pass deepCrawl:true for full category pagination)");
  }

  // 4. Economics — listings needed for target
  const top = scout.top?.[0];
  const avgNet = top?.net || intel.lethalCandidates?.[0]?.netAtCostRatio || 8;
  const econ = {
    sampleNet: netProfitPerSale({
      salePrice: top?.salePrice || intel.market.priceLadder.p50 || 45,
      productCost: (top?.salePrice || intel.market.priceLadder.p50 || 45) * costRatio,
    }),
    forecast: {
      expected: expectedDailyProfit({ listings: 300, str: assumedStr, avgNet }),
      needed: listingsNeeded({ targetDailyProfit, str: assumedStr, avgNet }),
      stress: stressForecast({
        listings: 300,
        str: assumedStr,
        avgNet,
        targetDailyProfit,
      }),
    },
  };
  note("Economics", `Avg net ~$${avgNet} → need ${econ.forecast.needed.listingsNeeded} listings for $${targetDailyProfit}/day`);

  // 5. Quality officer — merge lethal lists, de-dupe by title similarity / id
  const merged = mergeLethal(scout.top || [], intel.lethalCandidates || [], crawl?.topByPerceivedValue || []);
  note("Quality", `${merged.length} lethal candidates after scam/value merge`);

  // 6. Brain brief
  const brief = {
    verdict:
      merged.length >= 3
        ? "GO — enough high-PV candidates to test"
        : merged.length >= 1
          ? "CAUTION — thin lethal set; tighten query or crawl deeper"
          : "NO-GO — no candidates cleared quality + economics",
    whySuperiorToZikAutods: [
      "Fee-true net profit before you list (ZIK shows revenue proxies; we show cash)",
      "Scam/qty-spam/clickbait hard kills (most importers list junk)",
      "Perceived-value + upgrade/problem-solve ranking",
      "Zero-trust gates + CONDITIONAL flags when sold evidence missing",
      "Local/open orchestration — no $40–70/mo research SaaS tax at small scale",
    ],
    nextActions: [
      "Confirm wholesale cost with 2 suppliers (kill single-source)",
      "Cross-check sold comps in Terapeak (browser playbook)",
      "List 3–5 test SKUs only; log outcomes into LPROS conditioning loop",
      "Do not enable AutoDS-style auto-order until tracking SLA proven",
    ],
  };
  note("Brain", brief.verdict);

  return {
    mission: { q, categoryId, categoryLabel, minPrice, maxPrice, costRatio },
    elapsedMs: Date.now() - started,
    agents: log,
    scout: {
      counts: scout.counts,
      priceBand: scout.priceBand,
      top: scout.top?.slice(0, 8),
      forecast: scout.forecast,
    },
    intel,
    crawl: crawl
      ? { kept: crawl.kept, rawCount: crawl.rawCount, apiTotal: crawl.apiTotal, jsonlPath: crawl.jsonlPath }
      : null,
    economics: econ,
    lethalBoard: merged.slice(0, 25),
    brief,
  };
}

function mergeLethal(scoutTop, intelLethal, crawlTop) {
  const out = [];
  const seen = new Set();
  const push = (row, source) => {
    const key = (row.url || row.id || row.title || "").slice(0, 120);
    if (!key || seen.has(key)) return;
    if (row.scammy) return;
    seen.add(key);
    out.push({
      source,
      title: row.title,
      salePrice: row.salePrice ?? row.price,
      net: row.net ?? row.netAtCostRatio,
      marginPct: row.marginPct,
      perceivedValue: row.perceivedValue,
      psychFit: row.psychFit,
      url: row.url,
      decision: row.decision || "CANDIDATE",
      flags: row.flags || [],
    });
  };
  for (const r of scoutTop) push(r, "scout");
  for (const r of intelLethal) push(r, "intel");
  for (const r of crawlTop) push(r, "crawl");
  return out.sort(
    (a, b) =>
      (b.perceivedValue || 0) * Math.max(b.net || 0, 1) -
      (a.perceivedValue || 0) * Math.max(a.net || 0, 1)
  );
}
