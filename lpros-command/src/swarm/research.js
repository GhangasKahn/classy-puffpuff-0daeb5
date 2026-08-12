/**
 * Hermes-style research swarm — specialist agents, Brain merge.
 * Scout + Intel run in parallel; optional deep crawl; evidence harden; listing drafts.
 */
import { competitorIntel } from "../intel/competitor.js";
import { crawlCategory } from "../../../lpros/src/agents/crawl.js";
import { runResearchPipeline } from "../../../lpros/src/pipeline.js";
import { hardenCandidate } from "../../../lpros/src/core/evidence.js";
import { draftListing } from "../../../lpros/src/agents/listing.js";
import { logOutcome } from "../../../lpros/src/agents/outcome.js";
import {
  expectedDailyProfit,
  listingsNeeded,
  stressForecast,
  netProfitPerSale,
} from "../../../lpros/src/core/economics.js";

/**
 * @param {object} opts
 * @param {object} [opts.evidencePack] - Terapeak sold + dual supplier costs applied to board
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
  evidencePack = null,
  draftListings = true,
} = {}) {
  const started = Date.now();
  const log = [];
  const note = (agent, msg) => log.push({ ts: new Date().toISOString(), agent, msg });

  note("Brain", "Mission: find lethal, high-perceived-value SKUs — kill scammy dropship junk");

  // Scout + Intel in parallel (independent eBay calls)
  note("Scout", `Pipeline probe for "${q}"`);
  note("Intel", "Competitor density, price ladder, seller HHI");
  const [scout, intel] = await Promise.all([
    runResearchPipeline({
      category: categoryLabel,
      queries: [q],
      productCostRatio: costRatio,
      minPrice,
      maxPrice,
      targetDailyProfit,
      assumedStr,
    }),
    competitorIntel({
      q,
      categoryId,
      minPrice,
      maxPrice,
      limit: 100,
      productCostRatio: costRatio,
    }),
  ]);

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
  note(
    "Economics",
    `Avg net ~$${avgNet} → need ${econ.forecast.needed.listingsNeeded} listings for $${targetDailyProfit}/day`
  );

  let merged = mergeLethal(scout.top || [], intel.lethalCandidates || [], crawl?.topByPerceivedValue || []);
  note("Quality", `${merged.length} lethal candidates after scam/value merge`);

  // Evidence officer — optional Terapeak / dual-cost pack hardens the board
  let hardened = null;
  if (evidencePack && Object.keys(evidencePack).length) {
    note("Evidence", "Applying sold comps + dual supplier costs to lethal board");
    hardened = merged.slice(0, 12).map((row) => {
      const result = hardenCandidate(
        {
          title: row.title,
          salePrice: row.salePrice,
          price: row.salePrice,
          url: row.url,
          productCost: row.salePrice != null ? row.salePrice * costRatio : null,
          productCostEstimated: true,
          leadTimeDays: evidencePack.leadTimeDays ?? 7,
          soldEvidenceMissing: true,
          evidenceStatus: "partial",
          demandSources: ["ebay_browse"],
          activeCount: intel.market?.activeTotal || 20,
          density: intel.market?.density ?? 50,
          perceivedValue: row.perceivedValue,
          psychFit: row.psychFit,
          remorseRisk: 0.35,
          scammy: false,
          hasImages: true,
          hasItemSpecifics: true,
          str: assumedStr,
        },
        evidencePack,
        { minSalePrice: minPrice, maxSalePrice: maxPrice }
      );
      return {
        ...row,
        source: row.source,
        decision: result.decision,
        flags: result.remainingFlags,
        net: result.economics?.net ?? row.net,
        marginPct: result.economics?.marginPct ?? row.marginPct,
        cleared: result.cleared,
        verificationConfidence: result.verification?.verificationConfidence,
      };
    });
    merged = [
      ...hardened.filter((h) => h.decision === "PASS" || h.cleared),
      ...hardened.filter((h) => h.decision !== "PASS" && !h.cleared),
      ...merged.slice(12),
    ];
    const passN = hardened.filter((h) => h.decision === "PASS").length;
    note("Evidence", `${passN}/${hardened.length} board rows reached PASS after evidence`);
  }

  const listings = draftListings
    ? merged.slice(0, 5).map((row) => ({
        title: row.title,
        url: row.url,
        draft: draftListing(row),
      }))
    : [];
  if (listings.length) note("Copy", `Drafted ${listings.length} listing shells (deterministic)`);

  const passCount = merged.filter((m) => m.decision === "PASS").length;
  const brief = {
    verdict:
      passCount >= 1
        ? "GO — evidence-hardened PASS candidates ready to test-list"
        : merged.length >= 3
          ? "GO — enough high-PV candidates to test (still CONDITIONAL until sold+dual-cost)"
          : merged.length >= 1
            ? "CAUTION — thin lethal set; tighten query or crawl deeper"
            : "NO-GO — no candidates cleared quality + economics",
    passCount,
    conditionalCount: merged.filter((m) => m.decision === "CONDITIONAL").length,
    whySuperiorToZikAutods: [
      "Fee-true net profit before you list (ZIK shows revenue proxies; we show cash)",
      "Scam/qty-spam/clickbait hard kills (most importers list junk)",
      "Perceived-value + upgrade/problem-solve ranking",
      "Zero-trust gates + CONDITIONAL flags when sold evidence missing",
      "Evidence pack clears CONDITIONAL → PASS (Terapeak + dual quotes)",
      "Local/open orchestration — no $40–70/mo research SaaS tax at small scale",
    ],
    nextActions: evidencePack
      ? [
          "Publish 1–3 PASS drafts only; log sold/return outcomes into conditioning",
          "Keep fulfillment on HOLD until tracking SLA proven",
          "Do not enable AutoDS-style auto-order on CONDITIONAL SKUs",
        ]
      : [
          "Confirm wholesale cost with 2 suppliers (kill single-source)",
          "Cross-check sold comps in Terapeak (browser playbook) → POST evidence pack",
          "List 3–5 test SKUs only; log outcomes into LPROS conditioning loop",
          "Do not enable AutoDS-style auto-order until tracking SLA proven",
        ],
  };
  note("Brain", brief.verdict);

  const report = {
    mission: { q, categoryId, categoryLabel, minPrice, maxPrice, costRatio, evidenceApplied: Boolean(evidencePack) },
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
    listingDrafts: listings,
    brief,
  };

  logOutcome({
    type: "swarm_run",
    q,
    categoryId,
    verdict: brief.verdict,
    lethal: report.lethalBoard.length,
    passCount,
    elapsedMs: report.elapsedMs,
  });

  return report;
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
