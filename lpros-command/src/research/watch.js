/**
 * Research Watch — stepped live Browse session so the desk can show a VM
 * working in real time (search → ingest listings → getItem details).
 * Client-driven ticks work on local :8790 and Netlify (no hung async).
 */
import { persist, load, listKind, nid } from "../playground/store.js";
import { vmSnapshot } from "../playground/vm.js";
import { searchBrowseWithFallback } from "../intel/competitor.js";
import { getBrowseItem } from "../../../ebay-sold-items/src/ebay/browse.js";
import { config as ebayConfig } from "../../../ebay-sold-items/src/config.js";
import { deskFromResearch, emptyLiveHint, normalizeProduct } from "../http/marketRows.js";

const INGEST_BATCH = 4;

function now() {
  return new Date().toISOString();
}

/** Truncated JSON the desk can show as proof this is live Browse, not a CSV. */
export function clipProof(obj, max = 2200) {
  try {
    const s = JSON.stringify(obj, null, 2);
    return s.length > max ? `${s.slice(0, max)}\n…truncated` : s;
  } catch {
    return String(obj);
  }
}

function log(session, level, message, extra = {}) {
  const ev = { at: now(), level, message, phase: session.phase, ...extra };
  session.events = session.events || [];
  session.events.push(ev);
  if (session.events.length > 300) session.events.splice(0, session.events.length - 300);
  session.updatedAt = ev.at;
  return ev;
}

export function slimWatch(session) {
  if (!session) return null;
  const desk = deskFromResearch({ products: session.products, items: session.products });
  return {
    id: session.id,
    status: session.status,
    phase: session.phase,
    progress: session.progress,
    createdAt: session.createdAt,
    updatedAt: session.updatedAt,
    config: session.config,
    vm: session.vm,
    proof: session.proof,
    current: session.current,
    products: session.products,
    productCount: desk.productCount,
    productsWithImages: desk.productsWithImages,
    productsWithUrls: desk.productsWithUrls,
    market: session.market || null,
    error: session.error || null,
    emptyReason: session.emptyReason || null,
    events: (session.events || []).slice(-80),
    apiCalls: session.apiCalls || [],
    cursor: session.cursor,
    address: session.current?.url || session.apiCalls?.at(-1)?.path || "about:idle",
  };
}

export function getWatch(id) {
  return load("watch", id);
}

export function listWatches(limit = 20) {
  return listKind("watch", limit).map(slimWatch);
}

export function createWatchSession(input = {}) {
  if (input.dryRun) {
    throw Object.assign(
      new Error("Watch VM is live-only. Uncheck Dry-run — fixtures are not a research session."),
      { status: 400, code: "WATCH_LIVE_ONLY" }
    );
  }
  const appConfigured = Boolean(ebayConfig.appId && ebayConfig.certId);
  const snap = vmSnapshot();
  const session = {
    id: nid("watch"),
    status: "running",
    phase: "boot",
    progress: { phase: "boot", pct: 4 },
    createdAt: now(),
    updatedAt: now(),
    config: {
      q: input.q || "solid wood desk organizer",
      categoryId: input.categoryId || "25339",
      minPrice: Number(input.minPrice ?? 35),
      maxPrice: Number(input.maxPrice ?? 150),
      limit: Math.min(Number(input.limit ?? 40), 80),
      detailCount: Math.min(Number(input.detailCount ?? 8), 16),
      costRatio: Number(input.costRatio ?? 0.4),
    },
    vm: snap,
    proof: {
      source: "ebay_browse",
      api: "/buy/browse/v1/item_summary/search",
      detailApi: "/buy/browse/v1/item/{id}",
      env: ebayConfig.env,
      appConfigured,
      dryRun: false,
      hostname: snap.hostname,
      pid: snap.pid,
      node: snap.node,
      serverless: snap.serverless,
      notUploadedCsv: true,
      browseSnippet: null,
      itemSnippet: null,
    },
    raw: [],
    products: [],
    current: null,
    market: null,
    events: [],
    apiCalls: [],
    cursor: { ingest: 0, detail: 0 },
    error: null,
    emptyReason: null,
  };
  log(session, "info", `VM boot ${snap.hostname} · ${snap.platform} · pid ${snap.pid} · Node ${snap.node}`);
  persist("watch", session);
  return session;
}

function fail(session, message) {
  session.status = "failed";
  session.phase = "failed";
  session.error = message;
  session.emptyReason = message;
  session.progress = { phase: "failed", pct: session.progress?.pct || 0 };
  log(session, "error", message);
  persist("watch", session);
  return session;
}

async function stepBoot(session) {
  const ok = Boolean(ebayConfig.appId && ebayConfig.certId);
  session.proof.appConfigured = ok;
  session.proof.env = ebayConfig.env;
  log(
    session,
    ok ? "info" : "error",
    ok
      ? `eBay ${ebayConfig.env} app configured — Browse + getItem (not HTML scrape, not uploaded CSV)`
      : emptyLiveHint({ configured: false })
  );
  if (!ok) return fail(session, emptyLiveHint({ configured: false }));
  session.phase = "search";
  session.progress = { phase: "search", pct: 12 };
  log(session, "info", `Next: GET ${session.proof.api} q="${session.config.q}" category=${session.config.categoryId}`);
  persist("watch", session);
  return session;
}

async function stepSearch(session, searchFn) {
  const cfg = session.config;
  const call = {
    at: now(),
    method: "GET",
    host: "api.ebay.com",
    path: session.proof.api,
    query: { q: cfg.q, category_ids: cfg.categoryId, filter: `price:[${cfg.minPrice}..${cfg.maxPrice}]` },
  };
  session.apiCalls.push(call);
  log(session, "info", `Browse search "${cfg.q}" · $${cfg.minPrice}–$${cfg.maxPrice} · cat ${cfg.categoryId}`);
  persist("watch", session);
  const t0 = Date.now();
  try {
    const { page, attempt, error } = await searchBrowseWithFallback(
      {
        q: cfg.q,
        categoryId: cfg.categoryId,
        minPrice: cfg.minPrice,
        maxPrice: cfg.maxPrice,
        limit: cfg.limit,
      },
      searchFn
    );
    call.status = 200;
    call.ms = Date.now() - t0;
    call.sort = attempt?.sort || null;
    call.categoryIds = attempt?.categoryIds || null;
    call.total = page.total;
    call.sample = (page.items || []).length;
    const items = (page.items || [])
      .filter((i) => i.price != null && i.price >= cfg.minPrice && i.price <= cfg.maxPrice)
      .map((it) => normalizeProduct(it, { source: "ebay_browse", categoryId: cfg.categoryId }));
    session.raw = items;
    session.proof.lastAttempt = {
      sort: attempt?.sort || null,
      categoryIds: attempt?.categoryIds || null,
      total: page.total,
    };
    session.proof.browseSnippet = clipProof({
      host: "api.ebay.com",
      path: session.proof.api,
      status: 200,
      ms: call.ms,
      source: page.source || "ebay_browse",
      total: page.total,
      returned: items.length,
      items: items.slice(0, 2).map((i) => ({
        itemId: i.itemId || i.id,
        title: i.title,
        price: i.price,
        url: i.url,
        image: i.image,
      })),
    });
    log(
      session,
      items.length ? "info" : "error",
      items.length
        ? `Browse returned ${items.length} live listings (API total ${page.total ?? items.length}) · source=${page.source || "ebay_browse"} · first ${items[0]?.url || ""}`
        : error
          ? `Browse empty. Last error: ${error.message}`
          : emptyLiveHint()
    );
    if (!items.length) return fail(session, session.events.at(-1).message);
    session.phase = "ingest";
    session.progress = { phase: "ingest", pct: 28 };
    persist("watch", session);
    return session;
  } catch (e) {
    call.status = e.status || 500;
    call.ms = Date.now() - t0;
    call.error = e.message;
    return fail(session, `Browse failed: ${e.message}`);
  }
}

async function stepIngest(session) {
  const start = session.cursor.ingest || 0;
  const slice = session.raw.slice(start, start + INGEST_BATCH);
  for (const row of slice) {
    session.products.push({ ...row, source: "ebay_browse" });
    log(session, "info", `Ingest ${row.title?.slice(0, 70)} · $${Number(row.price || 0).toFixed(2)}`, {
      url: row.url,
      image: Boolean(row.image),
      itemId: row.itemId || row.id,
    });
  }
  session.cursor.ingest = start + slice.length;
  session.current = session.products[session.products.length - 1] || null;
  const pct = 28 + Math.round((session.cursor.ingest / Math.max(session.raw.length, 1)) * 32);
  session.progress = { phase: "ingest", pct: Math.min(pct, 60) };
  if (session.cursor.ingest >= session.raw.length) {
    session.phase = "detail";
    session.progress = { phase: "detail", pct: 62 };
    log(
      session,
      "info",
      `Board ready — ${session.products.length} products · ${session.products.filter((p) => p.image).length} images · ${session.products.filter((p) => p.url).length} URLs. Fetching getItem page content.`
    );
  }
  persist("watch", session);
  return session;
}

async function stepDetail(session, getItemFn) {
  const max = session.config.detailCount;
  const idx = session.cursor.detail || 0;
  if (idx >= max || idx >= session.products.length) {
    session.phase = "report";
    session.progress = { phase: "report", pct: 90 };
    persist("watch", session);
    return session;
  }
  const item = session.products[idx];
  const id = item.itemId || item.id;
  const fetch = getItemFn || getBrowseItem;
  const call = {
    at: now(),
    method: "GET",
    host: "api.ebay.com",
    path: `/buy/browse/v1/item/${id}`,
    itemId: id,
  };
  session.apiCalls.push(call);
  log(session, "info", `getItem ${id} — official listing page (images, specifics, description)`);
  persist("watch", session);
  const t0 = Date.now();
  try {
    const detail = await fetch(id);
    call.status = 200;
    call.ms = Date.now() - t0;
    const merged = normalizeProduct(
      { ...item, ...detail, image: detail.image || item.image, url: detail.url || item.url, detailFetched: true },
      { source: "ebay_browse" }
    );
    session.products[idx] = merged;
    session.current = merged;
    session.proof.itemSnippet = clipProof({
      host: "api.ebay.com",
      path: `/buy/browse/v1/item/${id}`,
      status: 200,
      ms: call.ms,
      itemId: id,
      title: merged.title,
      price: merged.price,
      url: merged.url,
      image: merged.image,
      imageCount: merged.imageCount,
      descriptionExcerpt: merged.descriptionExcerpt,
      itemSpecifics: merged.itemSpecifics,
    });
    log(session, "info", `Detail OK · ${(merged.descriptionExcerpt || "").slice(0, 80) || merged.specificsSummary || "no excerpt"}`, {
      url: merged.url,
      image: Boolean(merged.image),
      images: merged.imageCount,
    });
  } catch (e) {
    call.status = e.status || 500;
    call.ms = Date.now() - t0;
    call.error = e.message;
    item.detailFetched = false;
    item.detailError = e.message;
    session.current = item;
    log(session, "warn", `getItem failed for ${id}: ${e.message}`);
  }
  session.cursor.detail = idx + 1;
  session.progress = {
    phase: "detail",
    pct: 62 + Math.round(((idx + 1) / Math.max(max, 1)) * 26),
  };
  persist("watch", session);
  return session;
}

async function stepReport(session) {
  const desk = deskFromResearch({ products: session.products, items: session.products });
  session.market = {
    sampleSize: desk.productCount,
    productsWithImages: desk.productsWithImages,
    productsWithUrls: desk.productsWithUrls,
    priceBand: { min: session.config.minPrice, max: session.config.maxPrice },
    query: session.config.q,
    source: "ebay_browse",
  };
  session.phase = "done";
  session.status = "done";
  session.progress = { phase: "done", pct: 100 };
  log(
    session,
    "info",
    `Watch complete — ${desk.productCount} live products · ${desk.productsWithImages} images · ${desk.productsWithUrls} listing URLs. Not a CSV upload.`
  );
  persist("watch", session);
  return session;
}

export async function tickWatch(id, { n = 1, searchFn, getItemFn } = {}) {
  const session = load("watch", id);
  if (!session) throw Object.assign(new Error("watch session not found"), { status: 404 });
  if (session.status === "cancelled") return session;
  const steps = Math.min(Math.max(Number(n) || 1, 1), 12);
  for (let i = 0; i < steps; i += 1) {
    if (session.status !== "running") break;
    if (session.phase === "boot") await stepBoot(session);
    else if (session.phase === "search") await stepSearch(session, searchFn);
    else if (session.phase === "ingest") await stepIngest(session);
    else if (session.phase === "detail") await stepDetail(session, getItemFn);
    else if (session.phase === "report") await stepReport(session);
    else break;
  }
  return session;
}

export function cancelWatch(id) {
  const session = load("watch", id);
  if (!session) return null;
  session.status = "cancelled";
  session.phase = "cancelled";
  log(session, "warn", "Watch cancelled");
  persist("watch", session);
  return session;
}
