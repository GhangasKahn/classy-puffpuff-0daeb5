/**
 * Aggressive live red-team loop.
 * Official Browse + getItem only. Never HTML scrape. Never print secrets.
 *
 * Success: live items with images + URLs, hive agents communicating, build/tests green.
 */
import { config } from "../../ebay-sold-items/src/config.js";
import { getBrowseItem } from "../../ebay-sold-items/src/ebay/browse.js";
import { searchBrowseWithFallback, competitorIntel } from "../src/intel/competitor.js";
import { deskFromResearch } from "../src/http/marketRows.js";
import { routeApi } from "../src/http/router.js";
import { runWorkload, runSpecialist, listComms } from "../src/hive/index.js";
import { hostnameAllowed } from "../src/playground/browser.js";
import { packDir, CATALOG_TO_PACK } from "../../lpros-agents/src/loadPack.js";
import { packDir as barrelPackDir } from "../src/playground/index.js";

const QUERIES = [
  { q: "solid wood desk organizer", categoryId: "25339", minPrice: 35, maxPrice: 150 },
  { q: "bamboo desk organizer", categoryId: "25339", minPrice: 20, maxPrice: 200 },
  { q: "walnut tray", minPrice: 25, maxPrice: 180 },
  { q: "desk organizer wood", minPrice: 15, maxPrice: 250 },
  { q: "kitchen utensil crock", minPrice: 15, maxPrice: 80 },
  { q: "phone stand wood", minPrice: 10, maxPrice: 60 },
];

function secretOk() {
  return {
    env: config.env,
    appConfigured: Boolean(config.appId && config.certId),
    appIdLen: config.appId?.length || 0,
    certIdLen: config.certId?.length || 0,
    marketplace: config.marketplaceId,
    apiRoot: config.apiRoot,
  };
}

function scoreDesk(desk) {
  const products = desk.products || [];
  const withImg = products.filter((p) => p.image || (p.images || []).length);
  const withUrl = products.filter((p) => p.url);
  return {
    productCount: products.length,
    withImages: withImg.length,
    withUrls: withUrl.length,
    sample: products.slice(0, 3).map((p) => ({
      title: (p.title || "").slice(0, 80),
      price: p.price,
      hasImage: Boolean(p.image),
      hasUrl: Boolean(p.url),
      source: p.source || "",
      dryRun: Boolean(p.dryRun),
    })),
  };
}

async function probeBrowse(qrow) {
  const bugs = [];
  try {
    const { page, error } = await searchBrowseWithFallback(qrow);
    const n = page?.items?.length || 0;
    if (error) bugs.push(`fallback-error: ${error.message || error}`);
    if (!n) bugs.push(`empty-browse q="${qrow.q}"`);
    const withImg = (page.items || []).filter((i) => i.image || (i.images || []).length);
    const withUrl = (page.items || []).filter((i) => i.url);
    return {
      ok: n > 0 && withImg.length > 0 && withUrl.length > 0,
      n,
      withImg: withImg.length,
      withUrl: withUrl.length,
      bugs,
      title0: page.items?.[0]?.title?.slice(0, 80) || null,
    };
  } catch (e) {
    return { ok: false, n: 0, withImg: 0, withUrl: 0, bugs: [`throw: ${e.status || ""} ${e.message}`], title0: null };
  }
}

async function probeIntel(qrow) {
  const intel = await competitorIntel({ ...qrow, limit: 40 });
  const desk = deskFromResearch(intel, { query: qrow.q, categoryId: qrow.categoryId, configured: true });
  const scored = scoreDesk(desk);
  const bugs = [];
  if (intel.dryRun) bugs.push("intel marked dryRun on live path");
  if (!scored.productCount) bugs.push(`intel desk empty: ${desk.emptyReason || "no reason"}`);
  if (scored.productCount && !scored.withImages) bugs.push("intel products have no images");
  if (scored.productCount && !scored.withUrls) bugs.push("intel products have no urls");
  return { ok: scored.productCount > 0 && scored.withImages > 0 && scored.withUrls > 0, scored, bugs, emptyReason: desk.emptyReason };
}

async function probeLiveRoute(qrow) {
  const res = await routeApi({
    method: "POST",
    pathname: "/research/live",
    body: { ...qrow, limit: 40, detailCount: 4, details: true },
  });
  const desk = scoreDesk(res.body || {});
  const bugs = [];
  if (res.status !== 200) bugs.push(`live-route ${res.status}: ${res.body?.error || JSON.stringify(res.body).slice(0, 200)}`);
  if (desk.productCount && desk.sample.some((s) => s.dryRun)) bugs.push("live-route returned dry-run products");
  if (res.status === 200 && (!desk.withImages || !desk.withUrls)) bugs.push("live-route missing images or urls");
  return { ok: res.status === 200 && desk.productCount > 0 && desk.withImages > 0 && desk.withUrls > 0, status: res.status, desk, bugs };
}

async function probeGetItem(itemId) {
  if (!itemId) return { ok: false, bugs: ["no itemId"] };
  try {
    const it = await getBrowseItem(itemId);
    const hasImg = Boolean(it.image || (it.images || []).length);
    const hasUrl = Boolean(it.url || it.itemWebUrl);
    return { ok: hasImg && hasUrl, hasImg, hasUrl, title: (it.title || "").slice(0, 80) };
  } catch (e) {
    return { ok: false, bugs: [`getBrowseItem: ${e.status || ""} ${e.message}`] };
  }
}

async function probeHive() {
  const bugs = [];
  try {
    if (typeof packDir !== "function") bugs.push("packDir missing from loadPack");
    if (barrelPackDir("scout") !== packDir("scout")) bugs.push("playground barrel packDir mismatch");
    if (CATALOG_TO_PACK.brain !== "orchestrator") bugs.push("CATALOG_TO_PACK.brain");
  } catch (e) {
    bugs.push(`packDir import: ${e.message}`);
  }
  const crime = runSpecialist("redteam", { thesis: "HTML scrape eBay search to fill the desk" });
  if (crime.verdict !== "REFUSE") bugs.push(`redteam did not REFUSE scrape thesis (${crime.verdict})`);
  const gauntlet = await runWorkload("specialist-gauntlet", {
    dryRun: true,
    thesis: "ZIK screenshot means print",
    salePrice: 49,
    cost: 18,
  });
  if (!gauntlet.hiveBrief?.workersRan?.includes("redteam")) bugs.push("gauntlet missing redteam");
  if (!gauntlet.comms?.length && !listComms(5).length) bugs.push("no hive comms posted");
  const research = await runWorkload("research-gate", { dryRun: true, q: "solid wood desk organizer" });
  if (!research.hiveBrief?.workersRan?.includes("brain")) bugs.push("research-gate missing brain");
  if (!research.hiveBrief?.workersRan?.includes("scout")) bugs.push("research-gate missing scout");
  const replies = (research.comms || []).filter((m) => m.type === "reply");
  if (!replies.some((m) => m.from === "scout")) bugs.push("scout did not reply on hive bus");
  const brain = research.workers?.find((w) => w.agent === "brain");
  if (!(brain?.result?.hiveSoldiersSeen || []).includes("scout")) bugs.push("brain did not see scout");
  return {
    ok: bugs.length === 0,
    bugs,
    gauntletVerdict: gauntlet.hiveBrief?.verdict,
    workers: research.hiveBrief?.workersRan,
    comms: listComms(8).length,
    replies: replies.length,
  };
}

async function probeWatch(qrow) {
  const bugs = [];
  const created = await routeApi({
    method: "POST",
    pathname: "/research/watch",
    body: { q: qrow.q, categoryId: qrow.categoryId, minPrice: qrow.minPrice, maxPrice: qrow.maxPrice, limit: 20, detailCount: 2 },
  });
  if (created.status !== 200) {
    return { ok: false, bugs: [`watch create ${created.status}: ${created.body?.error || ""}`], phase: created.body?.phase };
  }
  if (/packDir/.test(created.body?.error || "")) bugs.push("watch crashed on packDir export");
  let session = created.body;
  let ticks = 0;
  while (session.status === "running" && ticks < 24) {
    const t = await routeApi({
      method: "POST",
      pathname: `/research/watch/${session.id}/tick`,
      body: { n: 2 },
    });
    ticks += 1;
    if (t.status !== 200) {
      bugs.push(`watch tick ${t.status}: ${t.body?.error || ""}`);
      break;
    }
    session = t.body;
    if (session.phase === "failed" || session.error) {
      bugs.push(`watch failed: ${session.error || session.emptyReason || session.phase}`);
      break;
    }
    if ((session.productCount || 0) > 0 && (session.productsWithImages || 0) > 0) break;
  }
  const ok =
    bugs.length === 0 &&
    (session.productCount || 0) > 0 &&
    (session.productsWithImages || 0) > 0 &&
    (session.productsWithUrls || 0) > 0;
  if (!ok && !bugs.length) bugs.push(`watch no products/images phase=${session.phase}`);
  return {
    ok,
    bugs,
    phase: session.phase,
    productCount: session.productCount,
    productsWithImages: session.productsWithImages,
    productsWithUrls: session.productsWithUrls,
    ticks,
  };
}

async function probeToS() {
  const bugs = [];
  if (hostnameAllowed("www.ebay.com") !== "ebay-item-only") bugs.push("ebay host not item-only");
  const blocked = await routeApi({
    method: "POST",
    pathname: "/playground/browser/fetch",
    body: { url: "https://www.ebay.com/sch/i.html?_nkw=desk" },
  });
  if (blocked.status !== 403) bugs.push(`search HTML fetch not 403 (${blocked.status})`);
  return { ok: bugs.length === 0, bugs };
}

async function main() {
  const report = {
    startedAt: new Date().toISOString(),
    secrets: secretOk(),
    loops: [],
    hive: null,
    tos: null,
    success: false,
    winner: null,
  };
  console.log(JSON.stringify({ phase: "secrets", ...report.secrets }));

  report.tos = await probeToS();
  console.log(JSON.stringify({ phase: "tos", ...report.tos }));

  report.hive = await probeHive();
  console.log(JSON.stringify({ phase: "hive", ...report.hive }));

  if (!report.secrets.appConfigured) {
    console.log(JSON.stringify({ phase: "abort", reason: "ebay not configured (no keys printed)" }));
    process.exitCode = 2;
    return report;
  }

  for (let i = 0; i < QUERIES.length; i++) {
    const qrow = QUERIES[i];
    const browse = await probeBrowse(qrow);
    if (!browse.ok) {
      report.loops.push({ i, q: qrow.q, browse });
      console.log(JSON.stringify({ phase: "loop", i, q: qrow.q, browse, bugs: browse.bugs }));
      continue;
    }
    let intel = null;
    let live = null;
    let watch = null;
    let item = null;
    try {
      intel = await probeIntel(qrow);
    } catch (e) {
      intel = { ok: false, bugs: [`intel throw: ${e.message}`] };
    }
    try {
      live = await probeLiveRoute(qrow);
    } catch (e) {
      live = { ok: false, bugs: [`live throw: ${e.message}`] };
    }
    try {
      watch = await probeWatch(qrow);
    } catch (e) {
      watch = { ok: false, bugs: [`watch throw: ${e.message}`] };
    }
    try {
      const { page } = await searchBrowseWithFallback(qrow);
      const first = page.items?.[0];
      if (first?.id) item = await probeGetItem(first.id);
    } catch (e) {
      item = { ok: false, bugs: [e.message] };
    }
    const loop = { i, q: qrow.q, browse, intel, live, watch, item };
    report.loops.push(loop);
    console.log(
      JSON.stringify({
        phase: "loop",
        i,
        q: qrow.q,
        browse,
        intelOk: intel?.ok,
        liveOk: live?.ok,
        watchOk: watch?.ok,
        itemOk: item?.ok,
        bugs: [
          ...(browse.bugs || []),
          ...(intel?.bugs || []),
          ...(live?.bugs || []),
          ...(watch?.bugs || []),
        ],
      })
    );
    if (browse.ok && intel?.ok && live?.ok && watch?.ok && report.hive.ok && report.tos.ok) {
      report.success = true;
      report.winner = qrow.q;
      break;
    }
  }

  report.finishedAt = new Date().toISOString();
  console.log(JSON.stringify({ phase: "done", success: report.success, winner: report.winner, hiveOk: report.hive.ok, tosOk: report.tos.ok, loops: report.loops.length }));
  process.exitCode = report.success ? 0 : 1;
  return report;
}

main().catch((e) => {
  console.error(JSON.stringify({ phase: "crash", error: e.message, status: e.status || null }));
  process.exitCode = 1;
});
